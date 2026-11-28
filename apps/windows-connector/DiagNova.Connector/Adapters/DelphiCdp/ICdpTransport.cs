using System.IO.Ports;
using System.Runtime.InteropServices;
using System.Text;

namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Transportabstraktion FTDI-Bulk / VCP / Simulator.
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
        _responses.Clear();
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
/// FTDI 0403:D6DA – Phase 22: versucht Windows-VCP (ftdi_sio/COM) wenn Port bekannt,
/// sonst ehrlicher Fail. Kein D2XX-Binary bundling; kein Auto-Flash.
/// </summary>
public sealed class FtdiCdpTransport : ICdpTransport
{
    private SerialPort? _port;
    private readonly string? _preferredPort;

    public FtdiCdpTransport(string? preferredComPort = null)
    {
        _preferredPort = preferredComPort;
    }

    public string Name => "ftdi-0403-d6da";
    public bool IsOpen => _port?.IsOpen == true;
    public bool IsSimulator => false;
    public string? LastErrorDe { get; private set; }
    public string? OpenedPort { get; private set; }

    public Task OpenAsync(CancellationToken ct = default)
    {
        // Nur auf Windows sinnvoll für lokale Adapter-HW
        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows) && string.IsNullOrWhiteSpace(_preferredPort))
        {
            LastErrorDe =
                "FTDI-Transport: Nicht-Windows ohne expliziten COM-Port. " +
                "Auf Windows: COM-Port der VID 0403/PID D6DA angeben oder inventarisieren. Kein Auto-Flash.";
            IsOpenAssertFalse();
            return Task.FromException(new InvalidOperationException(LastErrorDe));
        }

        var ports = SerialPort.GetPortNames();
        var candidate = _preferredPort;
        if (string.IsNullOrWhiteSpace(candidate))
        {
            // Ohne USB-Inventur: kein Ratespiel – ehrlich ablehnen
            LastErrorDe =
                "FTDI-Transport: kein preferred COM-Port gesetzt. " +
                "Bitte Port nach Inventur (0403:D6DA) übergeben. D2XX-Native optional später. " +
                $"Gefundene Ports: {string.Join(",", ports)}";
            return Task.FromException(new InvalidOperationException(LastErrorDe));
        }

        try
        {
            _port = new SerialPort(candidate!, 115200, Parity.None, 8, StopBits.One)
            {
                ReadTimeout = 3000,
                WriteTimeout = 3000,
                NewLine = "\r"
            };
            _port.Open();
            OpenedPort = candidate;
            LastErrorDe = null;
            return Task.CompletedTask;
        }
        catch (Exception ex)
        {
            LastErrorDe = $"FTDI/VCP Open fehlgeschlagen auf {candidate}: {ex.Message}";
            _port?.Dispose();
            _port = null;
            return Task.FromException(new InvalidOperationException(LastErrorDe));
        }
    }

    private void IsOpenAssertFalse() { /* helper for clarity */ }

    public Task CloseAsync(CancellationToken ct = default)
    {
        if (_port is not null)
        {
            if (_port.IsOpen) _port.Close();
            _port.Dispose();
            _port = null;
        }
        return Task.CompletedTask;
    }

    public Task WriteAsciiAsync(string framedCommand, CancellationToken ct = default)
    {
        if (_port is null || !_port.IsOpen)
            throw new InvalidOperationException("FTDI/VCP nicht geöffnet");
        var bytes = Encoding.ASCII.GetBytes(framedCommand);
        _port.Write(bytes, 0, bytes.Length);
        return Task.CompletedTask;
    }

    public Task<string> ReadAsciiFrameAsync(TimeSpan timeout, CancellationToken ct = default)
    {
        if (_port is null || !_port.IsOpen)
            throw new InvalidOperationException("FTDI/VCP nicht geöffnet");
        var deadline = DateTime.UtcNow + timeout;
        var sb = new StringBuilder();
        while (DateTime.UtcNow < deadline)
        {
            ct.ThrowIfCancellationRequested();
            try
            {
                var ch = _port.ReadExisting();
                if (!string.IsNullOrEmpty(ch))
                {
                    sb.Append(ch);
                    var s = sb.ToString();
                    var frames = CdpProtocol.SplitFrames(s);
                    if (frames.Count > 0)
                        return Task.FromResult(frames[0]);
                }
            }
            catch (TimeoutException)
            {
                // continue until deadline
            }
            Thread.Sleep(20);
        }
        throw new TimeoutException("Keine CDP-Antwort innerhalb Timeout");
    }

    /// <summary>Reconnect: Close + Open mit gleichem Preferred-Port. Kein Auto-Flash.</summary>
    public async Task ReconnectAsync(CancellationToken ct = default)
    {
        await CloseAsync(ct).ConfigureAwait(false);
        await OpenAsync(ct).ConfigureAwait(false);
    }

    public object TransportCapabilities() => new
    {
        vcp = true,
        d2xx_bundled = false,
        d2xx_optional_note_de = "FTDI D2XX nur bei rechtmäßiger Lizenz/Bindung – nicht gebündelt.",
        baud = 115200,
        preferred_port = _preferredPort,
        opened_port = OpenedPort,
        reconnect = true,
        auto_flash = false
    };

    public ValueTask DisposeAsync()
    {
        CloseAsync().GetAwaiter().GetResult();
        return ValueTask.CompletedTask;
    }
}
