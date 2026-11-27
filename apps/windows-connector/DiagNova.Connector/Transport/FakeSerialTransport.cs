using System.Text;

namespace DiagNova.Connector.Transport;

/// <summary>
/// Fake-Port für Unit-/IntegrationsTests. Simuliert ELM327 AT- und OBD-Antworten
/// über <see cref="Obd.ObdSimulatorResponses"/> (klar simulated).
/// </summary>
public sealed class FakeSerialTransport : ISerialTransport
{
    private readonly object _gate = new();
    private readonly StringBuilder _rxBuffer = new();
    private bool _open;
    private bool _disposed;
    private SerialTransportOptions? _options;

    /// <summary>Optionale Hook: wenn gesetzt, steuert die Antwort; sonst Default-ELM-AT-Echo.</summary>
    public Func<string, string>? ResponseFactory { get; set; }

    public string Name => "FakeSerialTransport";
    public bool IsOpen
    {
        get { lock (_gate) return _open; }
    }
    public string? PortName => _options?.PortName;

    public int OpenCount { get; private set; }
    public int CloseCount { get; private set; }
    public List<string> WrittenCommands { get; } = new();

    public Task OpenAsync(SerialTransportOptions options, CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        cancellationToken.ThrowIfCancellationRequested();
        lock (_gate)
        {
            if (_open)
            {
                throw new InvalidOperationException("Fake-Port bereits geöffnet (exklusiver Zugriff).");
            }
            _options = options;
            _open = true;
            OpenCount++;
            _rxBuffer.Clear();
        }
        return Task.CompletedTask;
    }

    public Task CloseAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        lock (_gate)
        {
            if (_open)
            {
                _open = false;
                CloseCount++;
                _rxBuffer.Clear();
            }
        }
        return Task.CompletedTask;
    }

    public Task WriteAsync(ReadOnlyMemory<byte> data, CancellationToken cancellationToken = default)
    {
        EnsureOpen(cancellationToken);
        var text = Encoding.ASCII.GetString(data.Span);
        EnqueueResponseFor(text);
        return Task.CompletedTask;
    }

    public async Task<ReadOnlyMemory<byte>> ReadAsync(int maxBytes, TimeSpan timeout, CancellationToken cancellationToken = default)
    {
        EnsureOpen(cancellationToken);
        var deadline = DateTime.UtcNow + timeout;
        while (DateTime.UtcNow < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            lock (_gate)
            {
                if (_rxBuffer.Length > 0)
                {
                    var take = Math.Min(maxBytes, _rxBuffer.Length);
                    var chunk = _rxBuffer.ToString(0, take);
                    _rxBuffer.Remove(0, take);
                    return Encoding.ASCII.GetBytes(chunk);
                }
            }
            await Task.Delay(5, cancellationToken).ConfigureAwait(false);
        }
        return ReadOnlyMemory<byte>.Empty;
    }

    public async Task<string> TransactTextAsync(string command, TimeSpan timeout, CancellationToken cancellationToken = default)
    {
        EnsureOpen(cancellationToken);
        var normalized = command.Trim();
        if (!normalized.EndsWith('\r'))
        {
            normalized += "\r";
        }

        lock (_gate)
        {
            WrittenCommands.Add(command.Trim());
        }

        EnqueueResponseFor(normalized);
        var deadline = DateTime.UtcNow + timeout;
        var sb = new StringBuilder();
        while (DateTime.UtcNow < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            lock (_gate)
            {
                if (_rxBuffer.Length > 0)
                {
                    sb.Append(_rxBuffer);
                    _rxBuffer.Clear();
                    var soFar = sb.ToString();
                    if (soFar.Contains('>') ||
                        soFar.Contains("OK", StringComparison.Ordinal) ||
                        soFar.Contains("ELM", StringComparison.OrdinalIgnoreCase) ||
                        soFar.Contains("NO DATA", StringComparison.OrdinalIgnoreCase) ||
                        soFar.Contains("STOPPED", StringComparison.OrdinalIgnoreCase) ||
                        soFar.Contains("UNABLE TO CONNECT", StringComparison.OrdinalIgnoreCase))
                    {
                        return soFar;
                    }
                }
            }
            await Task.Delay(5, cancellationToken).ConfigureAwait(false);
        }
        return sb.ToString();
    }

    private void EnqueueResponseFor(string written)
    {
        var cmd = written.Trim().TrimEnd('\r', '\n');
        string response;
        if (ResponseFactory is not null)
        {
            response = ResponseFactory(cmd);
        }
        else
        {
            response = DefaultElmResponse(cmd);
        }

        lock (_gate)
        {
            _rxBuffer.Append(response);
        }
    }

    private static string DefaultElmResponse(string cmd) =>
        Obd.ObdSimulatorResponses.ForCommand(cmd);

    private void EnsureOpen(CancellationToken cancellationToken)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        cancellationToken.ThrowIfCancellationRequested();
        lock (_gate)
        {
            if (!_open)
            {
                throw new InvalidOperationException("Fake-Port ist nicht geöffnet.");
            }
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        lock (_gate)
        {
            _open = false;
            _rxBuffer.Clear();
        }
    }

    public ValueTask DisposeAsync()
    {
        Dispose();
        return ValueTask.CompletedTask;
    }
}
