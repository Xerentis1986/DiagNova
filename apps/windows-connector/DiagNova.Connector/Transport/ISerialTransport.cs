namespace DiagNova.Connector.Transport;

/// <summary>
/// Abstraktion für seriellen Transport (echter Port oder Fake).
/// Exklusiver Zugriff, Timeout, Abbruch, Dispose – keine Fahrzeugsemantik.
/// </summary>
public interface ISerialTransport : IAsyncDisposable, IDisposable
{
    string Name { get; }
    bool IsOpen { get; }
    string? PortName { get; }

    Task OpenAsync(SerialTransportOptions options, CancellationToken cancellationToken = default);
    Task CloseAsync(CancellationToken cancellationToken = default);

    /// <summary>Sendet Rohbytes. Keine OBD-Interpretation.</summary>
    Task WriteAsync(ReadOnlyMemory<byte> data, CancellationToken cancellationToken = default);

    /// <summary>Liest bis Timeout oder Abbruch. Keine OBD-Interpretation.</summary>
    Task<ReadOnlyMemory<byte>> ReadAsync(int maxBytes, TimeSpan timeout, CancellationToken cancellationToken = default);

    /// <summary>Schreibt Text und liest Antwort bis zum Prompt-Zeichen oder Timeout (ELM-Vorbereitung).</summary>
    Task<string> TransactTextAsync(string command, TimeSpan timeout, CancellationToken cancellationToken = default);
}

public sealed class SerialTransportOptions
{
    public required string PortName { get; init; }
    public int BaudRate { get; init; } = 38400;
    public int DataBits { get; init; } = 8;
    public bool ExclusiveAccess { get; init; } = true;
    public TimeSpan WriteTimeout { get; init; } = TimeSpan.FromSeconds(2);
    public TimeSpan ReadTimeout { get; init; } = TimeSpan.FromSeconds(2);
}

public interface ISerialTransportFactory
{
    ISerialTransport Create(string kind);
}
