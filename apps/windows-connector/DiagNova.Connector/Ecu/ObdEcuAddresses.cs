namespace DiagNova.Connector.Ecu;

/// <summary>
/// ISO 15765-4 Standardadressen – keine erfundenen OEM-IDs.
/// </summary>
public static class ObdEcuAddresses
{
    public const int FunctionalRequest = 0x7DF;
    public const int PhysicalRequestMin = 0x7E0;
    public const int PhysicalRequestMax = 0x7E7;
    public const int PhysicalResponseMin = 0x7E8;
    public const int PhysicalResponseMax = 0x7EF;

    public static bool IsStandardResponse(string? ecuId)
    {
        if (!TryParseHex(ecuId, out var value))
        {
            return false;
        }
        return value is >= PhysicalResponseMin and <= PhysicalResponseMax;
    }

    public static string? Normalize(string? ecuId)
    {
        if (!TryParseHex(ecuId, out var value))
        {
            return null;
        }
        return value.ToString("X3");
    }

    public static string RoleHint(int responseId) => (responseId - PhysicalResponseMin) switch
    {
        0 => "Motor/ECM (OBD-Konvention)",
        1 => "Getriebe/TCM (OBD-Konvention, falls vorhanden)",
        var i => $"OBD-ECU-Slot {i}"
    };

    public static int? RequestForResponse(int responseId)
    {
        if (responseId is < PhysicalResponseMin or > PhysicalResponseMax)
        {
            return null;
        }
        return PhysicalRequestMin + (responseId - PhysicalResponseMin);
    }

    private static bool TryParseHex(string? ecuId, out int value)
    {
        value = 0;
        if (string.IsNullOrWhiteSpace(ecuId))
        {
            return false;
        }
        var s = ecuId.Trim().Replace("0x", "", StringComparison.OrdinalIgnoreCase).Replace("0X", "");
        return int.TryParse(s, System.Globalization.NumberStyles.HexNumber, null, out value);
    }
}
