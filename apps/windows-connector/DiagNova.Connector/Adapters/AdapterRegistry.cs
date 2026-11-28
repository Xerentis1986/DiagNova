using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;

namespace DiagNova.Connector.Adapters;

/// <summary>
/// Multi-Adapter-Verwaltung: Erkennung, manuelle Auswahl, Status, Wechsel.
/// Keine erfundenen Hardwareerfolge.
/// </summary>
public sealed class AdapterRegistry
{
    private readonly AdapterConnectionManager _connections;
    private readonly IDeviceInventory _inventory;
    private readonly DiagnosticProtocolLog _log;
    private string _selectedAdapterId = "simulator";

    public AdapterRegistry(
        AdapterConnectionManager connections,
        IDeviceInventory inventory,
        DiagnosticProtocolLog log)
    {
        _connections = connections;
        _inventory = inventory;
        _log = log;
    }

    public string SelectedAdapterId => _selectedAdapterId;

    public object ListProfiles() => new
    {
        selected_adapter_id = _selectedAdapterId,
        disclaimer_de =
            "Kompatibilitätsstatus ist ehrlich. hardware_tested/vehicle_tested überall false " +
            "bis Labornachweis. Keine pauschale Adapterunterstützung.",
        adapters = AdapterCatalog.All.Select(ToDto).ToArray()
    };

    public object? GetProfile(string adapterId)
    {
        var p = AdapterCatalog.Get(adapterId);
        return p is null ? null : ToDto(p);
    }

    public object Select(string adapterId)
    {
        var profile = AdapterCatalog.Get(adapterId)
            ?? throw new InvalidOperationException($"Unbekannter Adapter: {adapterId}");

        if (profile.Status is AdapterCompatibilityStatus.BlockedUndocumented
            or AdapterCompatibilityStatus.ManufacturerApprovalRequired
            or AdapterCompatibilityStatus.NotSupported)
        {
            _log.Warn("adapter", "Auswahl blockierter Adapter", adapterId);
            return new
            {
                ok = false,
                selected = false,
                adapter_id = adapterId,
                status = profile.Status.ToString(),
                message_de =
                    $"Adapter '{profile.DisplayNameDe}' ist nicht freigegeben ({profile.Status}). " +
                    profile.NotesDe
            };
        }

        // Delphi/CDP+: Auswahl für Geräte-Lese-Pfad erlaubt, aber hardware_tested=false
        if (profile.AdapterId == "delphi-autocom")
        {
            _selectedAdapterId = profile.AdapterId;
            _log.Info("adapter", "CDP+ gewählt (nur Safe-Reads / Sim)", _selectedAdapterId);
            return new
            {
                ok = true,
                selected = true,
                adapter_id = _selectedAdapterId,
                status = profile.Status.ToString(),
                vehicle_commands = false,
                hardware_tested = false,
                message_de =
                    "Delphi/CDP+ gewählt: Identitätssimulation und Protokollcodec verfügbar. " +
                    "CAN/Relais gesperrt. Live-FTDI erst nach Labor."
            };
        }

        if (profile.AdapterId == "vgate-icar-pro-2s")
        {
            _selectedAdapterId = profile.AdapterId;
            _log.Info("adapter", "Vgate iCar Pro 2S gewählt (ELM327 BT)", _selectedAdapterId);
            return new
            {
                ok = true,
                selected = true,
                adapter_id = _selectedAdapterId,
                status = profile.Status.ToString(),
                vehicle_commands = false,
                hardware_tested = false,
                product = "Vgate iCar Pro 2S",
                message_de =
                    "Vgate iCar Pro 2S gewählt: ELM327-AT-Pfad. " +
                    "Connection-Test mit port_name; Fahrzeuglabor ausstehend."
            };
        }

        _selectedAdapterId = profile.AdapterId;
        _log.Info("adapter", "Adapter manuell gewählt", _selectedAdapterId);
        return new
        {
            ok = true,
            selected = true,
            adapter_id = _selectedAdapterId,
            status = profile.Status.ToString(),
            message_de = $"Adapter gewählt: {profile.DisplayNameDe}. Hardwaretest ausstehend."
        };
    }

    public async Task<object> AutoDetectAsync(CancellationToken ct = default)
    {
        var snap = await _inventory.ScanAsync(ct).ConfigureAwait(false);
        var comPorts = snap.Devices
            .Where(d => d.Kind == DeviceKind.ComPort)
            .Select(d => d.PortName ?? d.DisplayName)
            .ToArray();
        var usb = snap.Devices
            .Where(d => d.Kind == DeviceKind.Usb)
            .Select(d => new { d.Id, d.DisplayName, d.VendorHint, d.NotesDe })
            .ToArray();
        var bt = snap.Devices
            .Where(d => d.Kind == DeviceKind.BluetoothSpp)
            .Select(d => d.DisplayName)
            .ToArray();

        var candidates = new List<object>
        {
            new
            {
                adapter_id = "simulator",
                reason_de = "Immer verfügbar (Simulation).",
                confidence = "high"
            }
        };

        if (comPorts.Length > 0)
        {
            candidates.Add(new
            {
                adapter_id = "elm327-stn",
                reason_de =
                    "COM-Port(s) gefunden – Kandidat für serielle ELM/STN-Geräte. " +
                    "OBD-DIAG/Delphi nicht automatisch zugeordnet.",
                confidence = "low",
                com_ports = comPorts
            });
        }

        candidates.Add(new
        {
            adapter_id = "obd-diag-2055",
            reason_de =
                "Falls VID/PID nach Hardware-Inventur DIAMEX/OBD-DIAG entsprechen: " +
                "nur Inventur, keine API. Status bleibt blocked bis Herstellerdoku.",
            confidence = "none",
            requires = "HardwareInventory + Herstellerfreigabe"
        });

        candidates.Add(new
        {
            adapter_id = "delphi-autocom",
            reason_de = "USB/BT möglich laut Delphi-Marketing – keine Drittanbieter-API erkannt.",
            confidence = "none",
            requires = "Hersteller-SDK / Freigabe"
        });

        _log.Info("adapter", "AutoDetect Inventar", $"com={comPorts.Length};usb={usb.Length};bt={bt.Length}");

        return new
        {
            selected_adapter_id = _selectedAdapterId,
            inventory = new
            {
                captured_at = snap.CapturedAt,
                platform = snap.Platform,
                com_ports = comPorts,
                usb,
                bluetooth = bt,
                limitations_de = snap.LimitationsDe
            },
            candidates,
            message_de =
                "Automatische Erkennung liefert nur Kandidaten. " +
                "Keine Hardwarefreigabe, kein Delphi/OBD-DIAG-Claim."
        };
    }

    public object ConnectionTest()
    {
        var profile = AdapterCatalog.Get(_selectedAdapterId)!;
        var status = _connections.GetStatus();

        if (profile.AdapterId is "obd-diag-2055" or "delphi-autocom")
        {
            return new
            {
                ok = false,
                adapter_id = profile.AdapterId,
                hardware_tested = false,
                vehicle_tested = false,
                message_de =
                    "Verbindungstest verweigert: Schnittstelle nicht dokumentiert / nicht freigegeben. " +
                    "Kein simuliertes „Erfolg“-Ergebnis."
            };
        }

        return new
        {
            ok = status.AdapterConnected || profile.AdapterId == "simulator",
            adapter_id = profile.AdapterId,
            adapter_connected = status.AdapterConnected,
            vehicle_connected = status.VehicleConnected,
            mode = status.Mode,
            hardware_tested = false,
            vehicle_tested = false,
            message_de = status.MessageDe + " (hardware_tested=false)"
        };
    }

    public object Capabilities()
    {
        var profile = AdapterCatalog.Get(_selectedAdapterId)!;
        return new
        {
            adapter_id = profile.AdapterId,
            status = profile.Status.ToString(),
            protocols = profile.Protocols,
            transports = profile.Transports,
            hardware_tested = false,
            vehicle_tested = false,
            blockers = profile.Blockers,
            notes_de = profile.NotesDe
        };
    }

    private static object ToDto(AdapterProfile p) => new
    {
        adapter_id = p.AdapterId,
        display_name_de = p.DisplayNameDe,
        vendor_hint = p.VendorHint,
        status = p.Status.ToString(),
        status_de = StatusDe(p.Status),
        hardware_tested = p.HardwareTested,
        vehicle_tested = p.VehicleTested,
        manufacturer_api_documented = p.ManufacturerApiDocumented,
        lawful_to_integrate = p.LawfulToIntegrate,
        protocols = p.Protocols,
        transports = p.Transports,
        blockers = p.Blockers,
        notes_de = p.NotesDe,
        docs = p.DocsPath
    };

    private static string StatusDe(AdapterCompatibilityStatus s) => s switch
    {
        AdapterCompatibilityStatus.TechnicallyIntegrated => "Technisch integriert",
        AdapterCompatibilityStatus.DriverPresent => "Treiber vorhanden",
        AdapterCompatibilityStatus.InterfaceIdentified => "Schnittstelle identifiziert",
        AdapterCompatibilityStatus.HardwareTestPassed => "Hardwaretest erfolgreich",
        AdapterCompatibilityStatus.VehicleTestPassed => "Fahrzeugtest erfolgreich",
        AdapterCompatibilityStatus.PartiallySupported => "Nur teilweise unterstützt",
        AdapterCompatibilityStatus.NotSupported => "Nicht unterstützt",
        AdapterCompatibilityStatus.ManufacturerApprovalRequired => "Herstellerfreigabe erforderlich",
        AdapterCompatibilityStatus.BlockedUndocumented => "Blockiert – undokumentiert",
        AdapterCompatibilityStatus.Planned => "Geplant",
        _ => s.ToString()
    };
}
