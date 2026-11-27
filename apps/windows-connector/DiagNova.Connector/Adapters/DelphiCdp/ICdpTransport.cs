namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Transportabstraktion FTDI-Bulk / Simulator.
/// Kein automatisches Öffnen gefährlicher Kanäle.
/// </summary>
public interface ICdpTransport : IAsyncDisposable
{
    string Name { get; }
    bool IsOpen { get; }
    bool IsSimulator { get; }
    Task OpenAsync(CancellationToken ct = default);
    Task CloseAsync(CancellationToken ct = default);
    Task WriteAsciiAsync(string framedCommand, CancellationToken ct = default);
    Task<string> ReadAsciiFrameAsync(TimeSpan timeout, CancellationToken ct = default);
}

/// <summary>
/// Fake-Transport mit dokumentierten Beispielantworten – für Unit-Tests und Demo.
/// </summary>
public sealed class FakeCdpTransport : ICdpTransport
{
    private readonly Queue<string> _responses = new();
    private readonly List<string> _sent = new();

    public string Name => "fake-cdp";
    public bool IsOpen { get; private set; }
    public bool IsSimulator => true;
    public IReadOnlyList<string> Sent => _sent;

    public void EnqueueResponse(string framed) => _responses.Enqueue(framed);

    public void LoadDocumentedIdentityResponses()
    {
        // Dokumentierte Beispiele aus Forschungsanalyse (ASCII-Antworten)
        _responses.Clear();
        // Reihenfolge je nach Aufruf – Caller enqueued gezielt oder wir mappen
    }

    public Task OpenAsync(CancellationToken ct = default)
    {
        IsOpen = true;
        return Task.CompletedTask;
    }

    public Task CloseAsync(CancellationToken ct = default)
    {
        IsOpen = false;
        return Task.CompletedTask;
    }

    public Task WriteAsciiAsync(string framedCommand, CancellationToken ct = default)
    {
        if (!IsOpen) throw new InvalidOperationException("Transport nicht geöffnet");
        _sent.Add(framedCommand);
        var code = CdpProtocol.ExtractCommandCode(framedCommand);
        // Auto-Antworten für Safe-Reads, wenn Queue leer und bekannt
        if (_responses.Count == 0)
        {
            var auto = code.ToUpperInvariant() switch
            {
                "200" => "*1 100251\r",
                "201" => "*1 1622\r",
                "203" => "*0 1362\r",
                "20A" => "*CDP+\r",
                _ => null
            };
            if (auto is not null) _responses.Enqueue(auto);
        }
        return Task.CompletedTask;
    }

    public Task<string> ReadAsciiFrameAsync(TimeSpan timeout, CancellationToken ct = default)
    {
        if (_responses.Count == 0)
            throw new TimeoutException("Keine Fake-Antwort in der Queue");
        return Task.FromResult(_responses.Dequeue());
    }

    public ValueTask DisposeAsync()
    {
        IsOpen = false;
        return ValueTask.CompletedTask;
    }
}

/// <summary>
/// FTDI 0403:D6DA – Platzhalter für Windows-Bulk/D2XX.
/// Öffnet in dieser Umgebung keine echte Hardware; dokumentiert den Pfad.
/// </summary>
public sealed class FtdiCdpTransport : ICdpTransport
{
    public string Name => "ftdi-0403-d6da";
    public bool IsOpen { get; private set; }
    public bool IsSimulator => false;
    public string? LastErrorDe { get; private set; }

    public Task OpenAsync(CancellationToken ct = default)
    {
        // Keine Libusb/D2XX-Bindung im Cloud-Agent – ehrlich ablehnen
        LastErrorDe =
            "FTDI-Transport: keine gebundene D2XX/libusb-Session in dieser Build-Umgebung. " +
            "Auf Windows mit Adapter: Gerät 0403:D6DA inventarisieren, ftdi_sio/VCP prüfen, " +
            "Bulk-Pipes erst nach Freigabe nutzen. Kein Automatik-Flash.";
        IsOpen = false;
        return Task.FromException(new InvalidOperationException(LastErrorDe));
    }

    public Task CloseAsync(CancellationToken ct = default)
    {
        IsOpen = false;
        return Task.CompletedTask;
    }

    public Task WriteAsciiAsync(string framedCommand, CancellationToken ct = default) =>
        throw new InvalidOperationException("FTDI nicht geöffnet");

    public Task<string> ReadAsciiFrameAsync(TimeSpan timeout, CancellationToken ct = default) =>
        throw new InvalidOperationException("FTDI nicht geöffnet");

    public ValueTask DisposeAsync() => ValueTask.CompletedTask;
}
