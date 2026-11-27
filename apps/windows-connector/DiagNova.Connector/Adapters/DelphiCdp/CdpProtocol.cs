using System.Globalization;
using System.Text;

namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Eigenständige ASCII-Framing-Implementierung für Autocom CDP+ / Delphi-DS150E-Varianten
/// auf Basis öffentlich dokumentierter Protokollbeobachtungen (Fakten, nicht Quellcode-Kopie).
/// Forschungsstand – nicht für alle Hardwareversionen bestätigt.
/// </summary>
public static class CdpProtocol
{
    public const byte StartByte = 0x2A; // '*'
    public const byte Terminator = 0x0D; // '\r'
    public const char FieldSep = '_';

    /// <summary>FTDI USB-ID der in smooker/obd untersuchten Variante.</summary>
    public const ushort DocumentedVendorId = 0x0403;
    public const ushort DocumentedProductId = 0xD6DA;

    /// <summary>Nur lesende Geräteabfragen – freigegeben für Simulator/Allowlist.</summary>
    public static readonly HashSet<string> SafeDeviceReadCommands = new(StringComparer.OrdinalIgnoreCase)
    {
        "200", // serial
        "201", // firmware
        "203", // battery voltage
        "20A", // device name
    };

    /// <summary>Gefährlich: Relais/CAN/Init – standardmäßig gesperrt.</summary>
    public static readonly HashSet<string> VehicleOrRelayCommands = new(StringComparer.OrdinalIgnoreCase)
    {
        "60b",
        "60bc",
        "668",
        "606",
        "608",
        "609",
        "918",
    };

    public static string EncodeCommand(string commandCode, params string[] args)
    {
        if (string.IsNullOrWhiteSpace(commandCode))
            throw new ArgumentException("commandCode required", nameof(commandCode));

        var sb = new StringBuilder();
        sb.Append((char)StartByte);
        sb.Append(commandCode.Trim());
        foreach (var a in args)
        {
            sb.Append(FieldSep);
            sb.Append(a);
        }
        sb.Append((char)Terminator);
        return sb.ToString();
    }

    public static byte[] EncodeCommandBytes(string commandCode, params string[] args) =>
        Encoding.ASCII.GetBytes(EncodeCommand(commandCode, args));

    public static string ExtractCommandCode(string framed)
    {
        var s = framed.Trim();
        if (s.StartsWith('*')) s = s[1..];
        if (s.EndsWith('\r')) s = s[..^1];
        var head = s.Split(FieldSep, 2)[0];
        return head;
    }

    public static bool IsSafeDeviceRead(string commandCode) =>
        SafeDeviceReadCommands.Contains(NormalizeCode(commandCode));

    public static bool IsVehicleOrRelayCommand(string commandCode)
    {
        var c = NormalizeCode(commandCode);
        if (VehicleOrRelayCommands.Contains(c)) return true;
        // prefix match for 918x self-test family
        return c.StartsWith("918", StringComparison.OrdinalIgnoreCase)
               || c.StartsWith("606", StringComparison.OrdinalIgnoreCase)
               || c.StartsWith("608", StringComparison.OrdinalIgnoreCase)
               || c.StartsWith("609", StringComparison.OrdinalIgnoreCase)
               || c.StartsWith("668", StringComparison.OrdinalIgnoreCase);
    }

    public static string NormalizeCode(string code)
    {
        var c = code.Trim().TrimStart('*');
        var cut = c.IndexOfAny(['_', '\r', ' ']);
        return cut < 0 ? c : c[..cut];
    }

    /// <summary>
    /// Parst Antworten der Form *1 100251\r, *0 1362\r, *CDP+\r, *121\r.
    /// </summary>
    public static CdpResponse ParseResponse(string raw)
    {
        var s = raw.Trim();
        if (s.Length == 0)
            return new CdpResponse(false, null, null, raw, "Leere Antwort");

        if (!s.StartsWith('*'))
            return new CdpResponse(false, null, null, raw, "Kein Startbyte *");

        var body = s.TrimStart('*').TrimEnd('\r', '\n', ' ');
        // "*1 100251" or "*0 1362" or "*CDP+" or "*121"
        var parts = body.Split(' ', 2, StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length == 2 && (parts[0] == "0" || parts[0] == "1"))
        {
            return new CdpResponse(true, parts[0], parts[1], raw, null);
        }

        return new CdpResponse(true, null, body, raw, null);
    }

    /// <summary>
    /// Batteriespannung: dokumentierte Beispiele *0 1362 / *1 1366 → 13.62 / 13.66 V
    /// (Wert / 100).
    /// </summary>
    public static bool TryParseBatteryVolts(string raw, out double volts)
    {
        volts = 0;
        var parsed = ParseResponse(raw);
        if (!parsed.Ok || string.IsNullOrWhiteSpace(parsed.Payload))
            return false;
        if (!int.TryParse(parsed.Payload, NumberStyles.Integer, CultureInfo.InvariantCulture, out var n))
            return false;
        volts = n / 100.0;
        return true;
    }

    public static IReadOnlyList<string> SplitFrames(string buffer)
    {
        var list = new List<string>();
        var start = 0;
        while (start < buffer.Length)
        {
            var star = buffer.IndexOf('*', start);
            if (star < 0) break;
            var cr = buffer.IndexOf('\r', star);
            if (cr < 0) break;
            list.Add(buffer[star..(cr + 1)]);
            start = cr + 1;
        }
        return list;
    }
}

public sealed record CdpResponse(
    bool Ok,
    string? Flag,
    string? Payload,
    string Raw,
    string? ErrorDe
);
