namespace DiagNova.Connector.Obd;

/// <summary>
/// Erlaubte OBD-/AT-Befehle für Phase 04 (Allowlist). Keine beliebigen Remote-Rohbefehle.
/// Mode 04 (Clear DTC) nur über <see cref="ClearDtcGate"/>.
/// </summary>
public static class ObdCommandAllowlist
{
    public static readonly HashSet<string> AtCommands = new(StringComparer.OrdinalIgnoreCase)
    {
        "ATZ", "ATE0", "ATL0", "ATH0", "ATH1", "ATI", "ATSP0", "ATSP6", "ATDP", "ATDPN",
        "ATRV", "ATWS", "ATST32"
    };

    /// <summary>Lesende Service-Requests (Hex ohne Spaces).</summary>
    public static readonly HashSet<string> ReadCommands = new(StringComparer.OrdinalIgnoreCase)
    {
        // Mode 01 – aktuelle PIDs + Bitmap
        "0100", "0101", "0104", "0105", "010C", "010D", "010F", "0110", "0111",
        "0120", "012F", "0140", "0142",
        // Mode 02 Freeze-Frame (Frame 00, DTC + gängige PIDs)
        "0200", "0202", "0204", "0205", "020C", "020D",
        // Mode 03/07/0A DTCs
        "03", "07", "0A",
        // Mode 09 VIN / CalID support
        "0900", "0902"
    };

    public const string ClearDtcCommand = "04";

    public static bool IsAllowedReadOrAt(string command)
    {
        var c = Normalize(command);
        if (c.StartsWith("AT", StringComparison.OrdinalIgnoreCase))
        {
            return AtCommands.Contains(c);
        }
        return ReadCommands.Contains(c);
    }

    public static bool IsClearDtc(string command) =>
        Normalize(command).Equals(ClearDtcCommand, StringComparison.OrdinalIgnoreCase);

    public static string Normalize(string command) =>
        string.Concat(command.Where(ch => !char.IsWhiteSpace(ch))).ToUpperInvariant();
}
