namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Kompatibilitätsmatrix Hardware/Firmware – ehrlich, ohne Vollabdeckungs-Claim.
/// Betreiber: Seriennummer beginnt mit 10; SW 2017.R3 und 2020.23 (Firmwarewechsel nötig).
/// </summary>
public static class CdpCompatibility
{
    public static object Matrix() => new
    {
        disclaimer_de =
            "Forschungsstand aus öffentlichen Protokollbeobachtungen (u. a. USB-ID 0403:D6DA). " +
            "Nicht für alle Clones/Firmware bestätigt. Keine vollständige Fahrzeugunterstützung.",
        usb = new
        {
            documented_vid = "0403",
            documented_pid = "D6DA",
            chip_hint = "FTDI front-end, STM32 inside (Forschung)",
            note_de = "Andere VID/PID möglich bei Varianten/Clones – Inventur erforderlich."
        },
        operator_hints = new
        {
            serial_prefix_10 = true,
            note_de =
                "Betreiber-Adapter: Seriennummer beginnt mit 10 (passt zu Beispielantwort *100251). " +
                "Software 2017.R3 und 2020.23 – beim Wechsel Firmwareupdate erforderlich " +
                "(DiagNova führt **kein** automatisches Firmwareupdate durch)."
        },
        software_pairs = new object[]
        {
            new
            {
                host_software = "2017.R3",
                firmware_policy = "paired",
                diagnova_auto_flash = false
            },
            new
            {
                host_software = "2020.23",
                firmware_policy = "paired_requires_update_when_switching",
                diagnova_auto_flash = false
            }
        },
        command_tiers = new
        {
            safe_device_read = CdpProtocol.SafeDeviceReadCommands.OrderBy(x => x).ToArray(),
            blocked_without_release = new[]
            {
                "60b/60bc (handshake/init)",
                "668 (CAN config / Relaisrisiko)",
                "606 (periodische CAN-Slots)",
                "608/609 (ECU/CAN)",
                "918x (Self-Test – nur mit Freigabe)"
            }
        },
        hardware_tested = false,
        vehicle_tested = false
    };

    public static bool SerialLooksLikeDocumentedFamily(string? serialPayload)
    {
        if (string.IsNullOrWhiteSpace(serialPayload)) return false;
        // Beispiel *100251 und Betreiber-Hinweis „beginnt mit 10“
        return serialPayload.StartsWith("10", StringComparison.Ordinal);
    }
}
