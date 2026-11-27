using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;

namespace DiagNova.Connector.Obd;

/// <summary>
/// OBD-II/EOBD-Sitzung über ELM327: Init, Protokollerkennung, PID-Bitmap,
/// Live-Daten, DTCs, Freeze-Frame, Readiness, VIN. Nur Allowlist-Befehle.
/// </summary>
public sealed class ObdSession
{
    private readonly ISerialTransport _transport;
    private readonly DiagnosticProtocolLog _log;
    private readonly bool _isSimulator;
    private readonly string _dataSource;
    private readonly TimeSpan _timeout;

    public string? ProtocolName { get; private set; }
    public string? ProtocolNumber { get; private set; }
    public bool VehicleLinked { get; private set; }
    public IReadOnlyList<int> SupportedPids { get; private set; } = Array.Empty<int>();

    public ObdSession(
        ISerialTransport transport,
        DiagnosticProtocolLog log,
        bool isSimulator,
        string dataSource,
        TimeSpan? timeout = null)
    {
        _transport = transport;
        _log = log;
        _isSimulator = isSimulator;
        _dataSource = dataSource;
        _timeout = timeout ?? TimeSpan.FromSeconds(3);
    }

    public async Task<object> InitializeAsync(CancellationToken ct = default)
    {
        EnsureOpen();
        var exchanges = new List<object>();

        foreach (var cmd in new[] { "ATZ", "ATE0", "ATL0", "ATH1", "ATSP0" })
        {
            var resp = await TransactAllowedAsync(cmd, ct).ConfigureAwait(false);
            exchanges.Add(new { command = cmd, kind = resp.Kind.ToString(), preview = Truncate(resp.Raw) });
            if (cmd == "ATZ" && resp.Kind is ObdResponseKind.Timeout or ObdResponseKind.Empty or ObdResponseKind.Malformed)
            {
                VehicleLinked = false;
                return new
                {
                    success = false,
                    data_source = _dataSource,
                    is_simulator = _isSimulator,
                    vehicle_connected = false,
                    message_de = "Adapter-Init fehlgeschlagen (ATZ).",
                    exchanges
                };
            }
        }

        // Protokollerkennung
        var search = await TransactAllowedAsync("0100", ct).ConfigureAwait(false);
        exchanges.Add(new { command = "0100", kind = search.Kind.ToString(), preview = Truncate(search.Raw) });

        if (search.Kind == ObdResponseKind.Ok && search.Frames.Count > 0)
        {
            VehicleLinked = true;
            var bitmapFrame = search.Frames.FirstOrDefault(f => f.Service == 0x41 && f.Pid == 0x00);
            if (bitmapFrame is not null && bitmapFrame.Data.Count >= 4)
            {
                SupportedPids = ObdResponseParser.ParsePidBitmap(0x00, bitmapFrame.Data.ToList());
            }
        }
        else if (search.Kind is ObdResponseKind.NoData or ObdResponseKind.UnableToConnect or ObdResponseKind.Timeout)
        {
            VehicleLinked = false;
            return new
            {
                success = false,
                data_source = _dataSource,
                is_simulator = _isSimulator,
                vehicle_connected = false,
                message_de = search.MessageDe,
                response_kind = search.Kind.ToString(),
                exchanges
            };
        }

        var dp = await TransactAllowedAsync("ATDP", ct).ConfigureAwait(false);
        ProtocolName = ExtractText(dp.Raw);
        exchanges.Add(new { command = "ATDP", kind = dp.Kind.ToString(), preview = Truncate(dp.Raw) });

        var dpn = await TransactAllowedAsync("ATDPN", ct).ConfigureAwait(false);
        ProtocolNumber = ExtractText(dpn.Raw);
        exchanges.Add(new { command = "ATDPN", kind = dpn.Kind.ToString(), preview = Truncate(dpn.Raw) });

        // Erweiterte Bitmap 0120 falls unterstützt
        if (SupportedPids.Contains(0x20))
        {
            var ext = await TransactAllowedAsync("0120", ct).ConfigureAwait(false);
            var f = ext.Frames.FirstOrDefault(x => x.Service == 0x41 && x.Pid == 0x20);
            if (f is not null && f.Data.Count >= 4)
            {
                var more = ObdResponseParser.ParsePidBitmap(0x20, f.Data.ToList());
                SupportedPids = SupportedPids.Concat(more).Distinct().OrderBy(x => x).ToArray();
            }
        }

        _log.Info("obd-session", "Init abgeschlossen",
            $"vehicle={VehicleLinked}; protocol={ProtocolName}; pids={SupportedPids.Count}");

        return new
        {
            success = VehicleLinked,
            data_source = _dataSource,
            is_simulator = _isSimulator,
            vehicle_connected = VehicleLinked,
            protocol_name = ProtocolName,
            protocol_number = ProtocolNumber,
            supported_pids = SupportedPids.Select(p => new { pid = p, pid_hex = $"0x{p:X2}" }),
            message_de = VehicleLinked
                ? "Adapter-Init und Protokollerkennung OK."
                : "Init ohne Fahrzeuglink.",
            exchanges
        };
    }

    public async Task<object> ReadLiveAsync(CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        var pids = new[] { 0x04, 0x05, 0x0C, 0x0D, 0x0F, 0x10, 0x11, 0x2F, 0x42 };
        var readings = new List<ObdPidReading>();
        var errors = new List<object>();

        foreach (var pid in pids)
        {
            if (SupportedPids.Count > 0 && !SupportedPids.Contains(pid))
            {
                readings.Add(new ObdPidReading(pid, ObdPidScaler.Definitions.GetValueOrDefault(pid)?.Name ?? $"pid_0x{pid:X2}",
                    ObdPidScaler.Definitions.GetValueOrDefault(pid)?.DescriptionDe ?? "Nicht unterstützt",
                    null, ObdPidScaler.Definitions.GetValueOrDefault(pid)?.Unit ?? "",
                    "not_supported", "unknown", DateTimeOffset.UtcNow));
                continue;
            }

            var cmd = $"01{pid:X2}";
            var resp = await TransactAllowedAsync(cmd, ct).ConfigureAwait(false);
            if (resp.Kind != ObdResponseKind.Ok)
            {
                errors.Add(new { pid, kind = resp.Kind.ToString(), message_de = resp.MessageDe });
                readings.Add(new ObdPidReading(pid,
                    ObdPidScaler.Definitions.GetValueOrDefault(pid)?.Name ?? $"pid_0x{pid:X2}",
                    ObdPidScaler.Definitions.GetValueOrDefault(pid)?.DescriptionDe ?? "",
                    null, ObdPidScaler.Definitions.GetValueOrDefault(pid)?.Unit ?? "",
                    resp.Kind.ToString().ToLowerInvariant(), "unknown", DateTimeOffset.UtcNow));
                continue;
            }

            foreach (var frame in resp.Frames.Where(f => f.Service == 0x41 && f.Pid == pid))
            {
                readings.Add(ObdPidScaler.Scale(pid, frame.Data, frame.EcuId));
            }
        }

        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            vehicle_connected = VehicleLinked,
            protocol_name = ProtocolName,
            timestamp = DateTimeOffset.UtcNow,
            readings,
            errors,
            message_de = "Live-Daten (Allowlist Mode 01)."
        };
    }

    public async Task<object> ReadDtcsAsync(CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        var all = new List<ObdDtcEntry>();
        var meta = new List<object>();

        foreach (var (cmd, expectedService) in new[] { ("03", 0x43), ("07", 0x47), ("0A", 0x4A) })
        {
            var resp = await TransactAllowedAsync(cmd, ct).ConfigureAwait(false);
            meta.Add(new { command = cmd, kind = resp.Kind.ToString(), multi_ecu = resp.MultiEcu, message_de = resp.MessageDe });
            if (resp.Kind == ObdResponseKind.NoData) continue;
            if (resp.Kind != ObdResponseKind.Ok)
            {
                continue;
            }
            foreach (var frame in resp.Frames.Where(f => f.Service == expectedService))
            {
                all.AddRange(ObdResponseParser.ParseDtcPayload(expectedService, frame.Data, frame.EcuId));
            }
            // Multi-ECU: auch Frames ohne exakten Service-Match über ECU trennen
            foreach (var frame in resp.Frames.Where(f => f.Service != expectedService && f.Service is 0x43 or 0x47 or 0x4A))
            {
                all.AddRange(ObdResponseParser.ParseDtcPayload(frame.Service!.Value, frame.Data, frame.EcuId));
            }
        }

        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            dtcs = all,
            by_ecu = all.GroupBy(d => d.EcuId).ToDictionary(g => g.Key, g => g.ToList()),
            permanent_clearable = false,
            meta,
            message_de = "DTCs stored/pending/permanent (permanente nicht löschbar)."
        };
    }

    public async Task<object> ReadFreezeFrameAsync(CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        var dtcResp = await TransactAllowedAsync("0202", ct).ConfigureAwait(false);
        string? dtc = null;
        if (dtcResp.Kind == ObdResponseKind.Ok)
        {
            var f = dtcResp.Frames.FirstOrDefault(x => x.Service == 0x42 && x.Pid == 0x02);
            if (f is not null && f.Data.Count >= 2)
            {
                dtc = ObdResponseParser.DecodeDtc(f.Data[0], f.Data[1]);
            }
        }
        else if (dtcResp.Kind == ObdResponseKind.NoData)
        {
            return new
            {
                data_source = _dataSource,
                is_simulator = _isSimulator,
                status = "no_data",
                dtc = (string?)null,
                readings = Array.Empty<object>(),
                message_de = "Kein Freeze-Frame (NO DATA) – nicht als null-Werte erfunden."
            };
        }

        var readings = new List<ObdPidReading>();
        foreach (var pid in new[] { 0x04, 0x05, 0x0C, 0x0D })
        {
            var resp = await TransactAllowedAsync($"02{pid:X2}", ct).ConfigureAwait(false);
            if (resp.Kind != ObdResponseKind.Ok) continue;
            foreach (var frame in resp.Frames.Where(f => f.Service == 0x42 && f.Pid == pid))
            {
                readings.Add(ObdPidScaler.Scale(pid, frame.Data, frame.EcuId));
            }
        }

        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            status = readings.Count > 0 || dtc is not null ? "ok" : "empty",
            dtc,
            readings,
            message_de = "Freeze-Frame Mode 02."
        };
    }

    public async Task<object> ReadReadinessAsync(CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        var resp = await TransactAllowedAsync("0101", ct).ConfigureAwait(false);
        if (resp.Kind == ObdResponseKind.NoData)
        {
            return new
            {
                data_source = _dataSource,
                status = "no_data",
                message_de = "Readiness NO DATA – nicht unterstützt oder keine Antwort."
            };
        }
        if (resp.Kind != ObdResponseKind.Ok)
        {
            return new
            {
                data_source = _dataSource,
                status = resp.Kind.ToString().ToLowerInvariant(),
                message_de = resp.MessageDe
            };
        }

        var frame = resp.Frames.FirstOrDefault(f => f.Service == 0x41 && f.Pid == 0x01);
        if (frame is null || frame.Data.Count < 4)
        {
            return new
            {
                data_source = _dataSource,
                status = "malformed",
                message_de = "Readiness-Frame unvollständig – Status malformed (kein null)."
            };
        }

        var a = frame.Data[0];
        var b = frame.Data[1];
        var c = frame.Data[2];
        var d = frame.Data[3];
        var mil = (a & 0x80) != 0;
        var dtcCount = a & 0x7F;
        var compression = (b & 0x08) != 0;

        var monitors = new Dictionary<string, object>();
        void AddCont(string name, int bit)
        {
            var available = (b & (1 << bit)) != 0;
            var incomplete = (b & (1 << (bit + 4))) != 0;
            monitors[name] = new
            {
                available,
                complete = available && !incomplete,
                status = available ? (incomplete ? "incomplete" : "complete") : "not_supported"
            };
        }
        AddCont("misfire", 0);
        AddCont("fuel_system", 1);
        AddCont("components", 2);

        if (!compression)
        {
            void AddSpark(string name, int bit)
            {
                var available = (c & (1 << bit)) != 0;
                var incomplete = (d & (1 << bit)) != 0;
                monitors[name] = new
                {
                    available,
                    complete = available && !incomplete,
                    status = available ? (incomplete ? "incomplete" : "complete") : "not_supported"
                };
            }
            AddSpark("catalyst", 0);
            AddSpark("heated_catalyst", 1);
            AddSpark("evap", 2);
            AddSpark("secondary_air", 3);
            AddSpark("o2_sensor", 5);
            AddSpark("o2_heater", 6);
            AddSpark("egr", 7);
        }

        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            status = "ok",
            mil_on = mil,
            dtc_count = dtcCount,
            ignition_type = compression ? "compression" : "spark",
            monitors,
            ecu_id = frame.EcuId,
            message_de = "Readiness Mode 01 PID 01."
        };
    }

    public async Task<object> ReadVinAsync(CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        var resp = await TransactAllowedAsync("0902", ct).ConfigureAwait(false);
        if (resp.Kind == ObdResponseKind.NoData)
        {
            return new
            {
                data_source = _dataSource,
                status = "unavailable",
                vin = (string?)null,
                supported = false,
                message_de = "VIN nicht unterstützt (NO DATA)."
            };
        }
        if (resp.Kind != ObdResponseKind.Ok)
        {
            return new
            {
                data_source = _dataSource,
                status = resp.Kind.ToString().ToLowerInvariant(),
                vin = (string?)null,
                supported = false,
                message_de = resp.MessageDe
            };
        }

        var bytes = new List<byte>();
        foreach (var frame in resp.Frames.Where(f => f.Service == 0x49 && (f.Pid is null or 0x02)))
        {
            bytes.AddRange(frame.Data);
        }
        // Fallback: alle Frame-Daten
        if (bytes.Count == 0)
        {
            foreach (var frame in resp.Frames) bytes.AddRange(frame.Data);
        }
        if (bytes.Count > 0 && bytes[0] <= 5) bytes = bytes.Skip(1).ToList();

        var vin = ObdResponseParser.DecodeVin(bytes);
        if (vin is null)
        {
            return new
            {
                data_source = _dataSource,
                status = "unavailable",
                vin = (string?)null,
                supported = false,
                message_de = "VIN nicht lesbar – Status unavailable (nicht als leerer String)."
            };
        }
        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            status = "ok",
            vin,
            supported = true,
            message_de = "VIN gelesen (Mode 09 PID 02)."
        };
    }

    public async Task<object> ClearDtcsAsync(ClearApproval approval, CancellationToken ct = default)
    {
        EnsureVehicleOrThrow();
        _log.Warn("obd-clear", "Mode 04 Clear DTC wird ausgeführt", approval.OperatorNote);

        // Vorher-Snapshot der DTCs (Nachprüfung vorbereiten)
        var before = await ReadDtcsAsync(ct).ConfigureAwait(false);

        var resp = await TransactAllowedAsync(ObdCommandAllowlist.ClearDtcCommand, ct, allowClear: true)
            .ConfigureAwait(false);

        // Kurze Pause + Nachprüfung
        await Task.Delay(200, ct).ConfigureAwait(false);
        var after = await ReadDtcsAsync(ct).ConfigureAwait(false);

        var success = resp.Kind == ObdResponseKind.Ok ||
                      (resp.Raw?.Contains("OK", StringComparison.OrdinalIgnoreCase) ?? false);

        return new
        {
            data_source = _dataSource,
            is_simulator = _isSimulator,
            success,
            response_kind = resp.Kind.ToString(),
            message_de = success
                ? "Mode 04 gesendet. Permanente DTCs bleiben ggf. bestehen – Nachprüfung siehe after."
                : $"Clear fehlgeschlagen: {resp.MessageDe}",
            warnings_honored = true,
            before,
            after,
            note_de = "Permanente DTCs (Mode 0A) sind nicht löschbar."
        };
    }

    public async Task<ObdParsedResponse> TransactAllowedAsync(
        string command,
        CancellationToken ct,
        bool allowClear = false)
    {
        var normalized = ObdCommandAllowlist.Normalize(command);
        if (ObdCommandAllowlist.IsClearDtc(normalized))
        {
            if (!allowClear)
            {
                throw new InvalidOperationException(
                    "Mode 04 (Clear DTC) nur über ClearDtcGate mit gültiger Freigabe.");
            }
        }
        else if (!ObdCommandAllowlist.IsAllowedReadOrAt(normalized))
        {
            _log.Warn("obd-allowlist", "Befehl abgelehnt", normalized);
            throw new InvalidOperationException($"Befehl nicht in Allowlist: {normalized}");
        }

        ct.ThrowIfCancellationRequested();
        string raw;
        try
        {
            raw = await _transport.TransactTextAsync(normalized, _timeout, ct).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            return ObdResponseParser.Parse(null, aborted: true);
        }

        var timedOut = string.IsNullOrWhiteSpace(raw) ||
                       (!raw.Contains('>') && !raw.Contains("OK", StringComparison.OrdinalIgnoreCase) &&
                        !raw.Contains("NO DATA", StringComparison.OrdinalIgnoreCase) &&
                        raw.Length < 3);

        // Wenn Timeout-Fenster abgelaufen und leer
        if (string.IsNullOrWhiteSpace(raw))
        {
            return ObdResponseParser.Parse(raw, timedOut: true);
        }

        var parsed = ObdResponseParser.Parse(raw, timedOut: false);
        _log.Info("obd-tx", $"{normalized} → {parsed.Kind}", Truncate(raw));
        return parsed;
    }

    private void EnsureOpen()
    {
        if (!_transport.IsOpen)
        {
            throw new InvalidOperationException("Transport nicht geöffnet.");
        }
    }

    private void EnsureVehicleOrThrow()
    {
        EnsureOpen();
        if (!VehicleLinked)
        {
            throw new InvalidOperationException(
                "Keine Fahrzeugverbindung – zuerst POST /obd/init ausführen.");
        }
    }

    private static string Truncate(string s) =>
        s.Length <= 100 ? s : s[..100] + "…";

    private static string ExtractText(string raw)
    {
        var lines = raw.Replace('\r', '\n').Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Select(l => l.Trim().TrimEnd('>').Trim())
            .Where(l => !string.IsNullOrEmpty(l) && !l.StartsWith("AT", StringComparison.OrdinalIgnoreCase) &&
                        !l.Equals("OK", StringComparison.OrdinalIgnoreCase));
        return string.Join(" ", lines);
    }
}
