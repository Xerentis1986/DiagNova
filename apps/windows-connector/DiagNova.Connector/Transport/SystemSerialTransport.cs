using System.IO.Ports;
using System.Text;

namespace DiagNova.Connector.Transport;

/// <summary>
/// Echter serieller Port mit exklusivem Zugriff, Timeouts, Abbruch und Dispose.
/// Öffnet den Port nur – sendet in Phase 03 keine OBD-Fahrzeugbefehle von außen.
/// </summary>
public sealed class SystemSerialTransport : ISerialTransport
{
    private readonly object _gate = new();
    private SerialPort? _port;
    private bool _disposed;

    public string Name => "SystemSerialTransport";
    public bool IsOpen
    {
        get { lock (_gate) return _port?.IsOpen == true; }
    }
    public string? PortName
    {
        get { lock (_gate) return _port?.PortName; }
    }

    public Task OpenAsync(SerialTransportOptions options, CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        cancellationToken.ThrowIfCancellationRequested();

        lock (_gate)
        {
            if (_port?.IsOpen == true)
            {
                throw new InvalidOperationException($"Port {_port.PortName} bereits geöffnet (exklusiver Zugriff).");
            }

            _port?.Dispose();
            var port = new SerialPort(options.PortName, options.BaudRate, Parity.None, options.DataBits, StopBits.One)
            {
                Handshake = Handshake.None,
                NewLine = "\r",
                ReadTimeout = (int)Math.Clamp(options.ReadTimeout.TotalMilliseconds, 1, int.MaxValue),
                WriteTimeout = (int)Math.Clamp(options.WriteTimeout.TotalMilliseconds, 1, int.MaxValue),
                Encoding = Encoding.ASCII,
                DtrEnable = true,
                RtsEnable = true
            };

            // Exclusive access: SerialPort.Open wirft IOException wenn Port belegt.
            port.Open();
            _port = port;
        }

        return Task.CompletedTask;
    }

    public Task CloseAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        lock (_gate)
        {
            if (_port?.IsOpen == true)
            {
                _port.Close();
            }
        }
        return Task.CompletedTask;
    }

    public Task WriteAsync(ReadOnlyMemory<byte> data, CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        cancellationToken.ThrowIfCancellationRequested();
        SerialPort port;
        lock (_gate)
        {
            port = _port ?? throw new InvalidOperationException("Port nicht geöffnet.");
            if (!port.IsOpen) throw new InvalidOperationException("Port nicht geöffnet.");
        }

        var buffer = data.ToArray();
        return Task.Run(() =>
        {
            cancellationToken.ThrowIfCancellationRequested();
            port.Write(buffer, 0, buffer.Length);
        }, cancellationToken);
    }

    public Task<ReadOnlyMemory<byte>> ReadAsync(int maxBytes, TimeSpan timeout, CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        SerialPort port;
        lock (_gate)
        {
            port = _port ?? throw new InvalidOperationException("Port nicht geöffnet.");
            if (!port.IsOpen) throw new InvalidOperationException("Port nicht geöffnet.");
        }

        return Task.Run(() =>
        {
            var deadline = DateTime.UtcNow + timeout;
            var buffer = new byte[Math.Max(1, maxBytes)];
            using var reg = cancellationToken.Register(() =>
            {
                try { port.DiscardInBuffer(); } catch { /* ignore */ }
            });

            while (DateTime.UtcNow < deadline)
            {
                cancellationToken.ThrowIfCancellationRequested();
                try
                {
                    if (port.BytesToRead > 0)
                    {
                        var read = port.Read(buffer, 0, Math.Min(buffer.Length, port.BytesToRead));
                        return (ReadOnlyMemory<byte>)buffer.AsMemory(0, read);
                    }
                }
                catch (TimeoutException)
                {
                    // weiter bis Deadline
                }
                Thread.Sleep(5);
            }
            return ReadOnlyMemory<byte>.Empty;
        }, cancellationToken);
    }

    public async Task<string> TransactTextAsync(string command, TimeSpan timeout, CancellationToken cancellationToken = default)
    {
        var payload = command.EndsWith('\r') ? command : command + "\r";
        await WriteAsync(Encoding.ASCII.GetBytes(payload), cancellationToken).ConfigureAwait(false);

        var deadline = DateTime.UtcNow + timeout;
        var sb = new StringBuilder();
        while (DateTime.UtcNow < deadline)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var remaining = deadline - DateTime.UtcNow;
            if (remaining <= TimeSpan.Zero) break;
            var chunk = await ReadAsync(256, remaining, cancellationToken).ConfigureAwait(false);
            if (chunk.Length > 0)
            {
                sb.Append(Encoding.ASCII.GetString(chunk.Span));
                if (sb.ToString().Contains('>'))
                {
                    break;
                }
            }
        }
        return sb.ToString();
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        lock (_gate)
        {
            try
            {
                if (_port?.IsOpen == true) _port.Close();
            }
            catch { /* ignore */ }
            _port?.Dispose();
            _port = null;
        }
    }

    public ValueTask DisposeAsync()
    {
        Dispose();
        return ValueTask.CompletedTask;
    }
}
