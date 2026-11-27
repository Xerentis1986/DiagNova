namespace DiagNova.Connector.Protocol;

/// <summary>
/// UDS ISO 14229 Negative Response Codes – Parser only, keine Schreibpfade.
/// </summary>
public static class UdsNrc
{
    private static readonly Dictionary<int, string> Names = new()
    {
        [0x10] = "generalReject",
        [0x11] = "serviceNotSupported",
        [0x12] = "subFunctionNotSupported",
        [0x13] = "incorrectMessageLengthOrInvalidFormat",
        [0x22] = "conditionsNotCorrect",
        [0x31] = "requestOutOfRange",
        [0x33] = "securityAccessDenied",
        [0x78] = "requestCorrectlyReceivedResponsePending",
        [0x7F] = "serviceNotSupportedInActiveSession",
    };

    public static string Decode(int nrc) =>
        Names.TryGetValue(nrc & 0xFF, out var name) ? name : $"unknown_nrc_0x{nrc & 0xFF:X2}";

    public static (int RequestSid, int Nrc, string Name)? Parse(IReadOnlyList<byte> data)
    {
        if (data.Count < 3 || data[0] != 0x7F)
        {
            return null;
        }
        var sid = data[1];
        var nrc = data[2];
        return (sid, nrc, Decode(nrc));
    }
}
