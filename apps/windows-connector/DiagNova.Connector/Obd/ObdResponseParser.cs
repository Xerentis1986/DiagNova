using System.Globalization;
using System.Text.RegularExpressions;

namespace DiagNova.Connector.Obd;

/// <summary>
/// Parst ELM327-ASCII-Antworten inkl. Mehr-ECU, NO DATA, Fehler und Negativantworten.
/// Unbekannte Werte werden nicht als null erfunden – Status bleibt explizit.
/// </summary>
public static class ObdResponseParser
{
    private static readonly (string Needle, ObdResponseKind Kind)[] ErrorMap =
    {
        ("NO DATA", ObdResponseKind.NoData),
        ("STOPPED", ObdResponseKind.Stopped),
        ("UNABLE TO CONNECT", ObdResponseKind.UnableToConnect),
        ("BUS ERROR", ObdResponseKind.BusError),
        ("CAN ERROR", ObdResponseKind.CanError),
        ("SEARCHING", ObdResponseKind.Searching),
    };

    public static ObdParsedResponse Parse(string? raw, bool timedOut = false, bool aborted = false)
    {
        if (aborted)
        {
            return new ObdParsedResponse(ObdResponseKind.Stopped, raw ?? "", Array.Empty<ObdEcuFrame>(),
                "Abbruch durch Benutzer oder Cancel.", Aborted: true);
        }
        if (timedOut)
        {
            return new ObdParsedResponse(ObdResponseKind.Timeout, raw ?? "", Array.Empty<ObdEcuFrame>(),
                "Timeout – keine vollständige Antwort vom Adapter.", TimedOut: true);
        }
        if (string.IsNullOrWhiteSpace(raw))
        {
            return new ObdParsedResponse(ObdResponseKind.Empty, raw ?? "", Array.Empty<ObdEcuFrame>(),
                "Leere Antwort – Status unbekannt (nicht als null gewertet).");
        }

        var text = raw;
        var upper = text.ToUpperInvariant();
        var lines = NormalizeLines(text);

        foreach (var (needle, kind) in ErrorMap)
        {
            if (!upper.Contains(needle, StringComparison.Ordinal)) continue;
            if (kind == ObdResponseKind.Searching && lines.Any(l => TryParseHexLine(l) is not null))
            {
                break;
            }
            if (kind is ObdResponseKind.NoData or ObdResponseKind.Stopped or ObdResponseKind.UnableToConnect
                or ObdResponseKind.BusError or ObdResponseKind.CanError)
            {
                return new ObdParsedResponse(kind, text, Array.Empty<ObdEcuFrame>(), MessageDe(kind));
            }
        }

        if (upper.Contains('?') && !lines.Any(l => TryParseHexLine(l) is not null))
        {
            return new ObdParsedResponse(ObdResponseKind.Malformed, text, Array.Empty<ObdEcuFrame>(),
                "Adapter meldet unverständlichen Befehl (?).");
        }

        var frames = new List<ObdEcuFrame>();
        foreach (var line in lines)
        {
            var lu = line.ToUpperInvariant();
            if (lu.StartsWith("AT", StringComparison.Ordinal) || lu == "OK" || lu.Contains("ELM")) continue;
            if (ErrorMap.Any(e => lu.Contains(e.Needle) && e.Kind != ObdResponseKind.Searching)) continue;

            var data = TryParseHexLine(line);
            if (data is null) continue;

            // ISO-TP first/consecutive frame PCI strip (einfach)
            if (data.Count >= 2 && (data[0] & 0xF0) == 0x10) data = data.Skip(1).ToList();
            else if (data.Count >= 1 && (data[0] & 0xF0) == 0x20) data = data.Skip(1).ToList();

            var frame = ParseFrameBytes(data);
            if (frame is not null) frames.Add(frame);
        }

        if (frames.Count == 0)
        {
            if (upper.Contains("SEARCHING", StringComparison.Ordinal))
            {
                return new ObdParsedResponse(ObdResponseKind.Searching, text, Array.Empty<ObdEcuFrame>(),
                    MessageDe(ObdResponseKind.Searching));
            }
            return new ObdParsedResponse(ObdResponseKind.Unknown, text, Array.Empty<ObdEcuFrame>(),
                "Antwort nicht als OBD-Frame erkennbar – Status unbekannt.");
        }

        if (frames.Any(f => f.IsNegative))
        {
            return new ObdParsedResponse(ObdResponseKind.Negative, text, frames, "Negative Antwort (7F) von ECU.");
        }

        var multi = frames.Select(f => f.EcuId).Distinct(StringComparer.OrdinalIgnoreCase).Count() > 1;
        return new ObdParsedResponse(ObdResponseKind.Ok, text, frames,
            multi ? "Antwort geparst – mehrere ECU-Antworten." : "Antwort geparst.");
    }

    public static IReadOnlyList<int> ParsePidBitmap(int basePid, IReadOnlyList<byte> data)
    {
        if (basePid % 0x20 != 0) throw new ArgumentException("basePid muss Vielfaches von 0x20 sein.");
        if (data.Count < 4) throw new ArgumentException("PID-Bitmap benötigt 4 Bytes.");
        var supported = new List<int>();
        for (var byteIndex = 0; byteIndex < 4; byteIndex++)
        {
            var b = data[byteIndex];
            for (var bit = 0; bit < 8; bit++)
            {
                if ((b & (1 << (7 - bit))) != 0)
                {
                    supported.Add(basePid + 1 + byteIndex * 8 + bit);
                }
            }
        }
        return supported;
    }

    public static string? DecodeDtc(byte high, byte low)
    {
        if (high == 0 && low == 0) return null;
        var system = ((high >> 6) & 0x03) switch
        {
            0 => "P",
            1 => "C",
            2 => "B",
            _ => "U"
        };
        var first = (high >> 4) & 0x03;
        var second = high & 0x0F;
        return $"{system}{first}{second:X}{low:X2}";
    }

    public static IReadOnlyList<ObdDtcEntry> ParseDtcPayload(int responseService, IReadOnlyList<byte> data, string ecuId)
    {
        var mode = responseService - 0x40;
        var status = mode switch
        {
            0x03 => "stored",
            0x07 => "pending",
            0x0A => "permanent",
            _ => "unknown"
        };
        var raw = data.ToList();
        if (raw.Count > 0 && raw[0] <= 16 && raw.Count == 1 + raw[0] * 2)
        {
            raw = raw.Skip(1).ToList();
        }
        else if (raw.Count % 2 == 1)
        {
            raw = raw.Skip(1).ToList();
        }

        var clearable = status != "permanent";
        var list = new List<ObdDtcEntry>();
        for (var i = 0; i + 1 < raw.Count; i += 2)
        {
            var code = DecodeDtc(raw[i], raw[i + 1]);
            if (code is null) continue;
            list.Add(new ObdDtcEntry(
                code,
                status,
                clearable,
                string.IsNullOrEmpty(ecuId) ? "unknown" : ecuId,
                clearable
                    ? $"DTC ({status})."
                    : "Permanenter DTC – nicht durch Mode 04 löschbar."
            ));
        }
        return list;
    }

    public static string? DecodeVin(IEnumerable<byte> data)
    {
        var chars = new List<char>();
        foreach (var b in data)
        {
            if (b == 0) continue;
            if (b is >= 32 and <= 126)
            {
                var ch = (char)b;
                if (IsVinChar(ch)) chars.Add(ch);
            }
        }
        var vin = new string(chars.ToArray());
        if (vin.Length >= 17)
        {
            var candidate = vin[..17];
            return candidate.All(IsVinChar) ? candidate : null;
        }
        return null;
    }

    private static bool IsVinChar(char ch) =>
        Regex.IsMatch(ch.ToString(), "^[A-HJ-NPR-Z0-9]$");

    private static List<string> NormalizeLines(string raw)
    {
        var lines = new List<string>();
        foreach (var line in raw.Replace('\r', '\n').Split('\n'))
        {
            var s = line.Trim();
            if (string.IsNullOrEmpty(s) || s == ">") continue;
            if (s.EndsWith('>')) s = s[..^1].Trim();
            if (!string.IsNullOrEmpty(s)) lines.Add(s);
        }
        return lines;
    }

    private static List<byte>? TryParseHexLine(string line)
    {
        var cleaned = line.Replace(":", " ").Replace(",", " ");
        var tokens = cleaned.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (tokens.Length == 0) return null;

        // ELM ATH1: erster Token oft 11-bit CAN-ID (3 Nibbles, z. B. 7E8)
        var bytes = new List<byte>();
        var start = 0;
        if (tokens[0].Length == 3 &&
            int.TryParse(tokens[0], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var canId) &&
            canId is >= 0x700 and <= 0x7FF)
        {
            // Als zwei Bytes 07 Ex speichern für einheitliches ECU-ID-Parsing
            bytes.Add((byte)((canId >> 8) & 0xFF));
            bytes.Add((byte)(canId & 0xFF));
            start = 1;
        }

        for (var i = start; i < tokens.Length; i++)
        {
            var t = tokens[i];
            if (t.Length is < 1 or > 2 ||
                !int.TryParse(t, NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var v))
            {
                // Fallback kompakt
                bytes = null;
                break;
            }
            bytes!.Add((byte)v);
        }

        if (bytes is { Count: > 0 }) return bytes;

        var compact = Regex.Replace(line, "[^0-9A-Fa-f]", "");
        // 7E8… → 3+even rest: normalize leading 3-nibble CAN id
        if (compact.Length >= 5 && compact.StartsWith("7E", StringComparison.OrdinalIgnoreCase))
        {
            // leave to token path failure only
        }
        if (compact.Length >= 2 && compact.Length % 2 == 0)
        {
            var list = new List<byte>();
            for (var i = 0; i < compact.Length; i += 2)
            {
                list.Add(byte.Parse(compact.AsSpan(i, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
            }
            return list;
        }
        return null;
    }

    private static ObdEcuFrame? ParseFrameBytes(List<byte> data)
    {
        if (data.Count == 0) return null;
        string ecuId = "unknown";
        var payload = data;

        if (data.Count >= 4 && data[0] == 0x07 && data[1] is >= 0xE8 and <= 0xEF)
        {
            ecuId = $"{data[0]:X2}{data[1]:X2}";
            payload = data.Skip(2).ToList();
        }
        else if (data.Count >= 3 && data[0] is >= 0xE8 and <= 0xEF)
        {
            ecuId = $"{data[0]:X2}";
            payload = data.Skip(1).ToList();
        }

        if (payload.Count == 0) return null;

        if (payload[0] == 0x7F)
        {
            int? sid = payload.Count > 1 ? payload[1] : null;
            int? nrc = payload.Count > 2 ? payload[2] : null;
            return new ObdEcuFrame(ecuId, 0x7F, sid, payload.Skip(3).ToArray(),
                string.Join(" ", data.Select(b => b.ToString("X2"))), nrc);
        }

        var service = (int)payload[0];
        int? pid = null;
        IReadOnlyList<byte> body;
        if (payload.Count >= 2 && service is 0x41 or 0x42 or 0x43 or 0x47 or 0x4A or 0x49)
        {
            // Mode 03/07/0A positive: 43 / 47 / 4A – zweites Byte oft Count, nicht PID
            if (service is 0x43 or 0x47 or 0x4A)
            {
                body = payload.Skip(1).ToArray();
            }
            else
            {
                pid = payload[1];
                body = payload.Skip(2).ToArray();
            }
        }
        else
        {
            body = payload.Skip(1).ToArray();
        }

        return new ObdEcuFrame(ecuId, service, pid, body,
            string.Join(" ", data.Select(b => b.ToString("X2"))), null);
    }

    private static string MessageDe(ObdResponseKind kind) => kind switch
    {
        ObdResponseKind.NoData => "NO DATA – ECU hat keine Daten geliefert.",
        ObdResponseKind.Timeout => "Timeout.",
        ObdResponseKind.Searching => "Protokollsuche läuft (SEARCHING…).",
        ObdResponseKind.BusError => "Bus-Fehler.",
        ObdResponseKind.CanError => "CAN-Fehler.",
        ObdResponseKind.Stopped => "Übertragung gestoppt.",
        ObdResponseKind.UnableToConnect => "Keine Verbindung zum Fahrzeugprotokoll.",
        _ => "Unbekannter Antwortstatus."
    };
}
