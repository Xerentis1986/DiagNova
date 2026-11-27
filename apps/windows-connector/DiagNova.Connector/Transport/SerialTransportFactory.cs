namespace DiagNova.Connector.Transport;

public sealed class SerialTransportFactory : ISerialTransportFactory
{
    public ISerialTransport Create(string kind) => kind.ToLowerInvariant() switch
    {
        "fake" or "simulator" => new FakeSerialTransport(),
        "system" or "serial" or "com" => new SystemSerialTransport(),
        _ => throw new ArgumentException($"Unbekannter Transport-Kind: {kind}", nameof(kind))
    };
}
