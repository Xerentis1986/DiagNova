namespace DiagNova.Connector.Obd;

/// <summary>
/// Dokumentierte Fake-/Simulator-Antwortvektoren für Parser- und Integrations-Tests.
/// Keine echten Fahrzeugdaten – klar als simulated gekennzeichnet.
/// </summary>
public static class ObdSimulatorResponses
{
    /// <summary>Demo-VIN nur für Simulator (enthält DEMO-Markierung im Geist der API-Seeds).</summary>
    public const string DemoVin = "WVWZZZ1JZXW000001";

    public static string ForCommand(string command)
    {
        var c = ObdCommandAllowlist.Normalize(command);
        return c switch
        {
            "ATZ" => "\r\rELM327 v1.5\r\n>",
            "ATE0" => "OK\r\n>",
            "ATL0" => "OK\r\n>",
            "ATH0" => "OK\r\n>",
            "ATH1" => "OK\r\n>",
            "ATI" => "ELM327 v1.5\r\n>",
            "ATSP0" => "OK\r\n>",
            "ATSP6" => "OK\r\n>",
            "ATDP" => "ISO 15765-4 (CAN 11/500)\r\n>",
            "ATDPN" => "A6\r\n>",
            "ATRV" => "12.6V\r\n>",
            "ATWS" => "\r\rELM327 v1.5\r\n>",
            "ATST32" => "OK\r\n>",

            // PID support bitmap 01-20: set common PIDs including 20 (next bitmap)
            // Bytes: BE 1F A8 13 → documented test vector
            "0100" => "7E8 41 00 BE 1F A8 13\r\n7E9 41 00 88 18 80 00\r\n>",
            "0120" => "7E8 41 20 A0 07 E1 00\r\n>",
            "0140" => "NO DATA\r\n>",

            // Readiness
            "0101" => "7E8 41 01 81 07 65 04\r\n>",

            // Live PIDs
            "0104" => "7E8 41 04 64\r\n>",           // load ~39%
            "0105" => "7E8 41 05 64\r\n>",           // 60°C
            "010C" => "7E8 41 0C 1F 40\r\n>",        // 2000 rpm
            "010D" => "7E8 41 0D 32\r\n>",           // 50 km/h
            "010F" => "7E8 41 0F 4B\r\n>",           // 35°C
            "0110" => "7E8 41 10 05 14\r\n>",        // 13.00 g/s
            "0111" => "7E8 41 11 2E\r\n>",           // throttle
            "012F" => "7E8 41 2F 9E\r\n>",           // fuel
            "0142" => "7E8 41 42 36 00\r\n>",        // 13.824 V

            // Freeze frame
            "0202" => "7E8 42 02 03 01\r\n>",        // DTC P0301
            "0204" => "7E8 42 04 50\r\n>",
            "0205" => "7E8 42 05 5A\r\n>",
            "020C" => "7E8 42 0C 1A 00\r\n>",
            "020D" => "7E8 42 0D 00\r\n>",
            "0200" => "7E8 42 00 BE 1F A8 13\r\n>",

            // DTCs multi-ECU stored
            "03" => "7E8 43 02 03 01 01 71\r\n7E9 43 01 04 20\r\n>",
            // Pending
            "07" => "7E8 47 01 01 28\r\n>",
            // Permanent (not clearable)
            "0A" => "7E8 4A 01 04 20\r\n>",

            // Clear
            "04" => "OK\r\n>",

            // VIN Mode 09
            "0900" => "7E8 49 00 55 00 00 00\r\n>",
            "0902" => $"7E8 49 02 01 {ToHex(DemoVin)}\r\n>",

            _ when c.StartsWith("AT", StringComparison.Ordinal) => "OK\r\n>",
            _ => "NO DATA\r\n>"
        };
    }

    private static string ToHex(string ascii) =>
        string.Join(" ", ascii.Select(ch => ((int)ch).ToString("X2")));
}
