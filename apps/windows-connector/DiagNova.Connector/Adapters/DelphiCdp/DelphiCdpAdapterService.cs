using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;

namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Integrationsfassade für den Connector: Erkennung, Identität (sim), Gates.
/// </summary>
public sealed class DelphiCdpAdapterService
{
    public const string ExpectedVidPid = "0403:D6DA";

    private readonly DiagnosticProtocolLog _log;
    private readonly IDeviceInventory _inventory;

    public DelphiCdpAdapterService(DiagnosticProtocolLog log, IDeviceInventory inventory)
    {
        _log = log;
        _inventory = inventory;
    }

    public object Status() => new
    {
        adapter_id = "delphi-autocom",
        protocol = "cdp-ascii-over-ftdi",
        documented_usb = $"0403:D6DA",
        manufacturer_api_official = false,
        research_sources = new[]
        {
            "https://github.com/smooker/obd (GPL-3.0 – nur Protokollfakten genutzt, kein Code kopiert)",
            "https://github.com/smooker/obd/blob/main/HOWTO.md",
            "https://github.com/smooker/obd/blob/main/ANALYSE.md"
        },
        safe_reads_implemented = CdpProtocol.SafeDeviceReadCommands.OrderBy(x => x).ToArray(),
        vehicle_commands_enabled = false,
        auto_firmware_update = false,
        hardware_tested = false,
        vehicle_tested = false,
        message_de =
            "Eigenständiges CDP+-Protokollmodul. Lesende Geräte-IDs im Simulator. " +
            "CAN/Relais gesperrt. Kein GPL-Code übernommen."
    };

    public object Compatibility() => CdpCompatibility.Matrix();

    public async Task<object> IdentifySimulatedAsync(CancellationToken ct = default)
    {
        await using var transport = new FakeCdpTransport();
        await using var session = new CdpSession(transport, _log, allowVehicleCommands: false);
        await session.OpenAsync(ct).ConfigureAwait(false);
        var id = await session.ReadIdentityAsync(ct).ConfigureAwait(false);
        return new
        {
            ok = true,
            identity = id,
            transport = transport.Name,
            sent = transport.Sent,
            note_de = "Nur Simulator – kein physischer Adapter in dieser Umgebung."
        };
    }

    public object TryOpenLive()
    {
        var t = new FtdiCdpTransport();
        try
        {
            t.OpenAsync().GetAwaiter().GetResult();
            return new { ok = true };
        }
        catch (Exception ex)
        {
            return new
            {
                ok = false,
                hardware_tested = false,
                message_de = ex.Message,
                next_steps_de = new[]
                {
                    "Windows: lsusb/Geräte-Manager – VID 0403 PID D6DA prüfen",
                    "Seriennummer (Befehl 200) – erwartet Präfix 10 laut Betreiber",
                    "Firmware (201) dokumentieren – kein Auto-Flash bei SW-Wechsel 2017↔2020",
                    "Erst Safe-Reads, CAN erst nach Freigabe"
                }
            };
        }
    }

    public object EncodeDemo() => new
    {
        examples = new object[]
        {
            new { cmd = "200", framed = CdpProtocol.EncodeCommand("200"), expect = "*1 100251\\r" },
            new { cmd = "201", framed = CdpProtocol.EncodeCommand("201"), expect = "*1 1622\\r" },
            new { cmd = "203", framed = CdpProtocol.EncodeCommand("203"), expect = "*0 1362\\r → 13.62 V" },
            new { cmd = "20A", framed = CdpProtocol.EncodeCommand("20A"), expect = "*CDP+\\r" },
        },
        blocked_example = new
        {
            cmd = "668",
            framed = CdpProtocol.EncodeCommand("668", "0", "500", "7E0", "7E8"),
            status = "blocked_without_release",
            reason_de = "CAN-Config kann Relais/Pins schalten – nicht freigegeben."
        }
    };

    /// <summary>
    /// Nichtinvasive Inventur: FTDI/CDP-Kandidaten (VID 0403 / PID D6DA).
    /// Keine Fahrzeugbefehle, kein Flash.
    /// </summary>
    public async Task<object> InventoryProbeAsync(CancellationToken ct = default)
    {
        var snap = await _inventory.ScanAsync(ct).ConfigureAwait(false);
        var candidates = snap.Devices
            .Where(d =>
            {
                var blob = $"{d.DisplayName}|{d.VendorHint}|{d.PortName}|{d.Kind}".ToLowerInvariant();
                return blob.Contains("0403")
                       || blob.Contains("d6da")
                       || blob.Contains("ftdi")
                       || blob.Contains("cdp")
                       || blob.Contains("autocom")
                       || blob.Contains("delphi");
            })
            .Select(d => new
            {
                d.Id,
                kind = d.Kind.ToString(),
                d.DisplayName,
                d.PortName,
                d.VendorHint
            })
            .ToArray();

        return new
        {
            ok = true,
            adapter_id = "delphi-autocom",
            expected_vid_pid = ExpectedVidPid,
            hardware_tested = false,
            vehicle_commands_sent = false,
            flash_attempted = false,
            candidates,
            limitations_de = snap.LimitationsDe,
            test_paths_de = new[]
            {
                "POST /adapters/delphi-cdp/inventory-probe",
                "POST /adapters/delphi-cdp/identify-sim (FakeCdp Safe-Reads)",
                "POST /adapters/delphi-cdp/open-live (nur mit physischem FTDI)",
                "GET /hardware/probe"
            },
            message_de =
                "Inventur nur. Live-Open und Fahrzeugbefehle getrennt; ohne HW: Kandidaten können leer sein."
        };
    }
}
