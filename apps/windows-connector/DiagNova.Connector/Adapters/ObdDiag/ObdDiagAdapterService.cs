namespace DiagNova.Connector.Adapters.ObdDiag;

/// <summary>
/// OBD-DIAG 2055+ / DIAMEX DX25 – Recherche-Modul.
/// Keine ELM-Annahme. Kein Fake-Live-Erfolg ohne inventarisierte Schnittstelle.
/// </summary>
public sealed class ObdDiagAdapterService
{
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
                "Variante „2055+“ im Betreiberbestand – Übereinstimmung mit DX25 hier nicht laborgeprüft."
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
            "GET /hardware/inventory am Connector ausführen",
            "VID/PID, Treibername, COM-Port notieren",
            "Kein ATZ/ELM-Test als Erfolg werten ohne Protokollnachweis",
            "Ergebnis in DIAGNOVA_OBD_DIAG_2055_STATUS.md nachtragen"
        },
        auto_connect = false,
        invent_protocol = false
    };
}
