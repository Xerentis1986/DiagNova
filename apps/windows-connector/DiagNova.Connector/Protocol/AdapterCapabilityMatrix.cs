namespace DiagNova.Connector.Protocol;

/// <summary>
/// Capability-Matrix: günstiger ELM ≠ DoIP/CAN-FD/J2534.
/// </summary>
public static class AdapterCapabilityMatrix
{
    public static object Matrix() => new
    {
        disclaimer_de =
            "Capability ≠ Freigabe. hardware_tested überall false. " +
            "Günstiger OBD-Adapter ist kein universelles DoIP/CAN-FD-Interface.",
        adapters = new object[]
        {
            new
            {
                adapter_id = "simulator",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j1979_obd"] = "supported_simulated",
                    ["iso_15765_4_obd_can"] = "supported_simulated",
                    ["iso_14229_uds"] = "partial_documented",
                    ["iso_13400_doip"] = "not_supported",
                    ["can_fd"] = "not_supported",
                    ["sae_j2534"] = "not_supported",
                    ["sae_j1939"] = "not_supported",
                }
            },
            new
            {
                adapter_id = "elm327-obd",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j1979_obd"] = "supported_code_untested_hw",
                    ["iso_15765_4_obd_can"] = "supported_code_untested_hw",
                    ["iso_13400_doip"] = "not_supported",
                    ["can_fd"] = "not_supported",
                    ["sae_j2534"] = "not_supported",
                },
                blocker = "BLK-HW"
            },
            new
            {
                adapter_id = "j2534-passthru",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j2534"] = "planned",
                    ["iso_13400_doip"] = "not_supported",
                },
                blocker = "BLK-HW",
                notes_de = "Nur Vorbereitung – keine DLL-Bindung."
            },
            new
            {
                adapter_id = "doip-ethernet",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["iso_13400_doip"] = "planned",
                },
                blocker = "BLK-HW",
                notes_de = "ELM ersetzt DoIP nicht."
            },
            new
            {
                adapter_id = "vgate-vlinker-mc-plus",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j1979_obd"] = "blocked",
                },
                blocker = "BLK-ADAPTER"
            },
            new
            {
                adapter_id = "obd-diag-2055",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j1979_obd"] = "blocked_undocumented_api",
                },
                blocker = "BLK-ADAPTER",
                notes_de = "moDiag: OBD-DIAG 2055 / DIAMEX DX 25 USB – keine freie API; ELM nicht angenommen."
            },
            new
            {
                adapter_id = "delphi-autocom",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["sae_j2534"] = "blocked",
                },
                blocker = "BLK-ADAPTER",
                notes_de = "DS150E USB/BT dokumentiert für Delphi-Software – keine Drittanbieter-API."
            },
            new
            {
                adapter_id = "rp1210-commercial",
                hardware_tested = false,
                protocols = new Dictionary<string, string>
                {
                    ["rp1210"] = "planned",
                    ["sae_j1939"] = "planned",
                    ["sae_j1708_j1587"] = "planned",
                    ["sae_j1979_obd"] = "not_supported",
                },
                blocker = "BLK-HW",
                notes_de = "Phase 19 Architektur – keine RP1210-DLL-Bindung. PKW-ELM ≠ RP1210."
            },
        }
    };
}
