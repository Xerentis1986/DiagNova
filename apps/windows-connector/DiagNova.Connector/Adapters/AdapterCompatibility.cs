namespace DiagNova.Connector.Adapters;

/// <summary>
/// Ehrliche Kompatibilitätsstufen – keine pauschalen Support-Claims.
/// </summary>
public enum AdapterCompatibilityStatus
{
    TechnicallyIntegrated,
    DriverPresent,
    InterfaceIdentified,
    HardwareTestPassed,
    VehicleTestPassed,
    PartiallySupported,
    NotSupported,
    ManufacturerApprovalRequired,
    BlockedUndocumented,
    Planned
}

public sealed record AdapterProfile(
    string AdapterId,
    string DisplayNameDe,
    string VendorHint,
    AdapterCompatibilityStatus Status,
    bool HardwareTested,
    bool VehicleTested,
    bool ManufacturerApiDocumented,
    bool LawfulToIntegrate,
    IReadOnlyList<string> Protocols,
    IReadOnlyList<string> Transports,
    IReadOnlyList<string> Blockers,
    string NotesDe,
    string? DocsPath
);

public static class AdapterCatalog
{
    public static IReadOnlyList<AdapterProfile> All { get; } =
    [
        new(
            "simulator",
            "Simulator / Fake-Port",
            "DiagNova",
            AdapterCompatibilityStatus.TechnicallyIntegrated,
            HardwareTested: false,
            VehicleTested: false,
            ManufacturerApiDocumented: true,
            LawfulToIntegrate: true,
            Protocols: ["sae_j1979_obd", "iso_15765_4"],
            Transports: ["fake-serial"],
            Blockers: [],
            NotesDe: "Simuliert getestet. Kein Hardwareanspruch.",
            DocsPath: null
        ),
        new(
            "elm327-stn",
            "ELM327 / STN (dokumentierte AT/ST)",
            "OBDLink / ScanTool (Doku)",
            AdapterCompatibilityStatus.PartiallySupported,
            HardwareTested: false,
            VehicleTested: false,
            ManufacturerApiDocumented: true,
            LawfulToIntegrate: true,
            Protocols: ["sae_j1979_obd", "iso_15765_4"],
            Transports: ["com", "fake-serial"],
            Blockers: ["BLK-HW"],
            NotesDe: "Nur für nachweislich kompatible Hardware. Keine ELM-Annahme für OBD-DIAG ohne Nachweis.",
            DocsPath: "docs/DIAGNOVA_ADAPTER_RESEARCH.md"
        ),
        new(
            "obd-diag-2055",
            "OBD-DIAG 2055+ / DIAMEX DX25 (Recherche)",
            "OBD-DIAG / DIAMEX (laut moDiag)",
            AdapterCompatibilityStatus.BlockedUndocumented,
            HardwareTested: false,
            VehicleTested: false,
            ManufacturerApiDocumented: false,
            LawfulToIntegrate: false,
            Protocols: [],
            Transports: ["usb-com-candidate"],
            Blockers: ["BLK-ADAPTER", "BLK-HW"],
            NotesDe: "moDiag listet OBD-DIAG 2055 / DIAMEX DX 25 als USB-Interface. Keine freie Entwickler-API nachgewiesen. ELM-Kompatibilität nicht angenommen.",
            DocsPath: "docs/DIAGNOVA_OBD_DIAG_2055_STATUS.md"
        ),
        new(
            "delphi-autocom",
            "Delphi DS150E / Autocom (Recherche)",
            "Delphi Autoparts",
            AdapterCompatibilityStatus.ManufacturerApprovalRequired,
            HardwareTested: false,
            VehicleTested: false,
            ManufacturerApiDocumented: false,
            LawfulToIntegrate: false,
            Protocols: [],
            Transports: ["usb", "bluetooth-spp-candidate"],
            Blockers: ["BLK-ADAPTER"],
            NotesDe: "Offizielle Software nutzt USB/BT – belegt keine Drittanbieter-API. Keine proprietären DLLs ohne Rechte.",
            DocsPath: "docs/DIAGNOVA_DELPHI_AUTOCOM_STATUS.md"
        ),
        new(
            "j2534-passthru",
            "J2534 PassThru (Abstraktion)",
            "SAE J2534 kompatible Geräte",
            AdapterCompatibilityStatus.Planned,
            HardwareTested: false,
            VehicleTested: false,
            ManufacturerApiDocumented: true,
            LawfulToIntegrate: true,
            Protocols: ["sae_j2534"],
            Transports: ["j2534-dll"],
            Blockers: ["BLK-HW"],
            NotesDe: "Modulare Transportebene vorbereitet. Bedeutet nicht, dass Delphi J2534 unterstützt.",
            DocsPath: "docs/DIAGNOVA_CONNECTOR_DRIVER_MATRIX.md"
        ),
    ];

    public static AdapterProfile? Get(string adapterId) =>
        All.FirstOrDefault(a => string.Equals(a.AdapterId, adapterId, StringComparison.OrdinalIgnoreCase));
}
