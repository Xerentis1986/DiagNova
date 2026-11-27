namespace DiagNova.Connector.Obd;

public enum ObdResponseKind
{
    Ok,
    NoData,
    Timeout,
    Searching,
    BusError,
    CanError,
    Stopped,
    UnableToConnect,
    Negative,
    Unknown,
    Empty,
    Malformed
}

public sealed record ObdEcuFrame(
    string EcuId,
    int? Service,
    int? Pid,
    IReadOnlyList<byte> Data,
    string RawHex,
    int? NegativeCode
)
{
    public bool IsNegative => Service == 0x7F || NegativeCode is not null;
}

public sealed record ObdParsedResponse(
    ObdResponseKind Kind,
    string Raw,
    IReadOnlyList<ObdEcuFrame> Frames,
    string MessageDe,
    bool TimedOut = false,
    bool Aborted = false
)
{
    public bool MultiEcu =>
        Frames.Select(f => f.EcuId).Distinct(StringComparer.OrdinalIgnoreCase).Count() > 1;
}

public sealed record ObdPidReading(
    int Pid,
    string Name,
    string DescriptionDe,
    double? Value,
    string Unit,
    string Status,
    string? EcuId,
    DateTimeOffset Timestamp
);

public sealed record ObdDtcEntry(
    string Code,
    string Status,
    bool Clearable,
    string EcuId,
    string MessageDe
);

public sealed record ObdSessionSnapshot(
    string DataSource,
    bool IsSimulator,
    bool AdapterConnected,
    bool VehicleConnected,
    string? ProtocolName,
    string? ProtocolNumber,
    IReadOnlyList<int> SupportedPids,
    IReadOnlyList<ObdPidReading> LiveReadings,
    IReadOnlyList<ObdDtcEntry> Dtcs,
    object? Readiness,
    object? FreezeFrame,
    object? Vin,
    string MessageDe,
    DateTimeOffset Timestamp
);
