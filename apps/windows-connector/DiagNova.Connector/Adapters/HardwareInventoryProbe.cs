using System.Runtime.InteropServices;
using DiagNova.Connector.Discovery;

namespace DiagNova.Connector.Adapters;

/// <summary>
/// Read-only Hardwarediagnose: COM/USB/BT inventarisieren.
/// Keine Firmware-, Steuergeräte- oder Pairing-Änderungen.
/// </summary>
public sealed class HardwareInventoryProbe
{
    private readonly IDeviceInventory _inventory;

    public HardwareInventoryProbe(IDeviceInventory inventory)
    {
        _inventory = inventory;
    }

    public async Task<object> ProbeAsync(CancellationToken ct = default)
    {
        var snap = await _inventory.ScanAsync(ct).ConfigureAwait(false);
        return new
        {
            purpose_de =
                "Windows-Hardwarediagnose für Adapter-Identifikation (OBD-DIAG/Delphi etc.). " +
                "Nur Lesen – keine Firmware-/Fahrzeugänderungen.",
            os = new
            {
                platform = RuntimeInformation.OSDescription,
                architecture = RuntimeInformation.OSArchitecture.ToString(),
                is_windows = OperatingSystem.IsWindows()
            },
            captured_at = snap.CapturedAt,
            inventory_platform = snap.Platform,
            devices = snap.Devices.Select(d => new
            {
                d.Id,
                kind = d.Kind.ToString(),
                d.DisplayName,
                d.PortName,
                d.Address,
                d.VendorHint,
                d.IsPaired,
                d.IsAvailable,
                d.Source,
                d.NotesDe
            }),
            limitations_de = snap.LimitationsDe,
            guidance_de = new[]
            {
                "1. Exakte Gerätebezeichnung und Hardwareversion notieren.",
                "2. Im Geräte-Manager Treibername, VID/PID, COM-Port prüfen.",
                "3. Ergebnisse mit Herstellerdoku abgleichen – keine ELM-Annahme.",
                "4. Bei OBD-DIAG 2055+: DIAMEX DX25-Hinweis aus moDiag ist kein API-Nachweis.",
                "5. Bei Delphi DS150E: USB/BT laut Marketing ≠ Drittanbieter-SDK."
            },
            manufacturer_inquiry_draft_de = ManufacturerInquiryDraft(),
            hardware_tested = false,
            vehicle_commands_sent = false
        };
    }

    public static string ManufacturerInquiryDraft() =>
        """
        Betreff: Anfrage Entwickler-/Integrationsschnittstelle für Diagnoseadapter

        Sehr geehrte Damen und Herren,

        wir entwickeln die Werkstattsoftware DiagNova und prüfen eine rechtmäßige
        Anbindung Ihres Diagnoseadapters. Bitte teilen Sie uns mit:

        1. Exakte Modell- und Firmwarebezeichnung unserer Gerätevariante
        2. USB Vendor ID / Product ID sowie empfohlene Windows-Treiber
        3. Ob eine dokumentierte serielle Befehlsschnittstelle, SDK oder J2534-API
           für Drittanbieter kommerziell lizenziert werden kann
        4. Lizenz- und Nutzungsbedingungen für eine Integration in Drittsoftware
        5. Ob Bluetooth-SPP oder nur herstellereigene Protokolle vorgesehen sind

        Wir nehmen keine Reverse-Engineering-Maßnahmen an Lizenzschutz vor und
        ändern keine Firmware.

        Mit freundlichen Grüßen
        DiagNova Entwicklung
        """;
}
