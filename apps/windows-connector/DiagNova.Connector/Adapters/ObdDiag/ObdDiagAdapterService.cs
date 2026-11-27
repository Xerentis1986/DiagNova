using DiagNova.Connector.Discovery;

namespace DiagNova.Connector.Adapters.ObdDiag;

/// <summary>
/// OBD-DIAG 2055+ / DIAMEX DX25 – Recherche + nichtinvasive Inventur.
/// Keine ELM-Annahme. Kein Fake-Live-Erfolg ohne inventarisierte Schnittstelle.
/// </summary>
public sealed class ObdDiagAdapterService
{
    private readonly IDeviceInventory _inventory;

    public ObdDiagAdapterService(IDeviceInventory inventory)
    {
        _inventory = inventory;
    }

    public object Status() => new
    {
        adapter_id = "obd-diag-2055",
        compatibility = AdapterCompatibilityStatus.BlockedUndocumented.ToString(),
        manufacturer_api_documented = false,
        elm327_assumed = false,
        hardware_tested = false,
        vehicle_tested = false,
        research = new
        {
            modig_hint = "moDiag listet OBD-DIAG 2055 / DIAMEX DX 25 (USB)",
            sources = new[]
            {
                "https://modiag.de/expert.htm",
                "https://www.modiag.de/ultimate.htm"
            },
            variant_note_de =
                "Variante „2055+“ – Übereinstimmung mit DX25 hier nicht laborgeprüft."
        },
        required_before_driver = new[]
        {
            "Lokale USB-Inventur (VID/PID, Treiber, COM)",
            "Protokollnachweis (ELM nur bei positivem Test)",
            "Kommerzielle Nutzungsbedingungen / SDK"
        },
        message_de =
            "Profil vorhanden, Treiber blockiert bis Schnittstelle inventarisiert und dokumentiert ist."
    };

    public object ProbeGuidance() => new
    {
        steps_de = new[]
        {
            "Adapter an Windows-PC anschließen",
            "POST /adapters/obd-diag/inventory-probe ausführen",
            "VID/PID, Treibername, COM-Port notieren",
            "Kein ATZ/ELM-Test als Erfolg werten ohne Protokollnachweis",
            "Ergebnis in DIAGNOVA_OBD_DIAG_2055_STATUS.md nachtragen"
        },
        auto_connect = false,
        invent_protocol = false
    };

    /// <summary>
    /// Nichtinvasive Inventur – speichert keine Fahrzeugbefehle.
    /// </summary>
    public async Task<object> InventoryProbeAsync(CancellationToken ct = default)
    {
        var snap = await _inventory.ScanAsync(ct).ConfigureAwait(false);
        var usbHints = snap.Devices
            .Where(d =>
            {
                var kind = d.Kind.ToString();
                return kind.Contains("Usb", StringComparison.OrdinalIgnoreCase)
                       || kind.Contains("Com", StringComparison.OrdinalIgnoreCase)
                       || kind.Contains("Serial", StringComparison.OrdinalIgnoreCase);
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
            hardware_tested = false,
            vehicle_commands_sent = false,
            elm327_assumed = false,
            candidates = usbHints,
            limitations_de = snap.LimitationsDe,
            message_de =
                "Nur Inventur. Kein Protokolltreiber. Treiber bleibt BlockedUndocumented " +
                "bis VID/PID und Schnittstelle nachgewiesen sind.",
            next_de = new[]
            {
                "Vendor/Product-ID aus Geräte-Manager notieren",
                "Falls COM: Portname dokumentieren",
                "Hersteller-API/Lizenz klären bevor Integration"
            }
        };
    }
}
