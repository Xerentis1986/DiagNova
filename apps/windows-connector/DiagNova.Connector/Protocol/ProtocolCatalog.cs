namespace DiagNova.Connector.Protocol;

/// <summary>
/// Protokollkatalog Phase 05 – Status ehrlich, getrennt von Transport/Adapter.
/// </summary>
public static class ProtocolCatalog
{
    public static object Summary() => new
    {
        phase = 5,
        disclaimer_de = "Status bezieht sich auf Code/Simulator – nicht auf Hardwarefreigabe.",
        layers = new[]
        {
            new { id = "transport", description_de = "Seriell/Fake; später DoIP/J2534." },
            new { id = "protocol", description_de = "OBD/ISO-TP/UDS/KWP – Semantik." },
            new { id = "adapter", description_de = "Capability-Matrix pro Hardware." },
            new { id = "vehicle_definition", description_de = "Nur verifizierte ECU-Adressen." }
        },
        protocols = new object[]
        {
            Entry("sae_j1979_obd", "OBD-II/EOBD", "simulated_tested", "protocol"),
            Entry("iso_15765_2_isotp", "ISO-TP", "parser_only", "protocol"),
            Entry("iso_15765_4_obd_can", "OBD on CAN Adressen", "simulated_tested", "protocol"),
            Entry("iso_14229_uds", "UDS", "parser_only", "protocol"),
            Entry("iso_9141_2", "ISO 9141-2", "documented_prep", "protocol"),
            Entry("iso_14230_kwp2000", "KWP2000", "documented_prep", "protocol"),
            Entry("sae_j1850", "J1850", "documented_prep", "protocol"),
            Entry("iso_11898_can", "CAN", "documented_prep", "transport"),
            Entry("can_fd", "CAN FD", "blocked", "transport"),
            Entry("iso_13400_doip", "DoIP", "documented_prep", "transport"),
            Entry("sae_j2534", "J2534", "documented_prep", "adapter"),
            Entry("iso_22900_dpdu", "D-PDU", "documented_prep", "adapter"),
            Entry("sae_j1939", "J1939", "planned_later", "protocol"),
            Entry("rp1210", "RP1210", "planned_later", "adapter"),
        }
    };

    private static object Entry(string id, string name, string status, string layer) => new
    {
        id,
        name,
        status,
        layer
    };
}
