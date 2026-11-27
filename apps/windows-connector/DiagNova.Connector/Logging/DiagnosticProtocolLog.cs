using System.Collections.Concurrent;

namespace DiagNova.Connector.Logging;

public enum ProtocolLogLevel
{
    Debug,
    Info,
    Warn,
    Error
}

public sealed record ProtocolLogEntry(
    DateTimeOffset Timestamp,
    ProtocolLogLevel Level,
    string Category,
    string Message,
    string? Detail = null
);

/// <summary>
/// Ringpuffer für Transport-/Status-Ereignisse. Keine Fahrzeugbefehl-Payloads mit Schreibsemantik.
/// </summary>
public sealed class DiagnosticProtocolLog
{
    private readonly ConcurrentQueue<ProtocolLogEntry> _entries = new();
    private readonly int _capacity;
    private int _count;

    public DiagnosticProtocolLog(int capacity = 500)
    {
        _capacity = Math.Max(50, capacity);
    }

    public void Info(string category, string message, string? detail = null) =>
        Add(ProtocolLogLevel.Info, category, message, detail);

    public void Warn(string category, string message, string? detail = null) =>
        Add(ProtocolLogLevel.Warn, category, message, detail);

    public void Error(string category, string message, string? detail = null) =>
        Add(ProtocolLogLevel.Error, category, message, detail);

    public void Debug(string category, string message, string? detail = null) =>
        Add(ProtocolLogLevel.Debug, category, message, detail);

    public void Add(ProtocolLogLevel level, string category, string message, string? detail = null)
    {
        _entries.Enqueue(new ProtocolLogEntry(DateTimeOffset.UtcNow, level, category, message, detail));
        var newCount = Interlocked.Increment(ref _count);
        while (newCount > _capacity && _entries.TryDequeue(out _))
        {
            newCount = Interlocked.Decrement(ref _count);
        }
    }

    public IReadOnlyList<ProtocolLogEntry> Snapshot(int max = 100)
    {
        return _entries.Reverse().Take(Math.Max(1, max)).Reverse().ToList();
    }

    public void Clear()
    {
        while (_entries.TryDequeue(out _)) { }
        Interlocked.Exchange(ref _count, 0);
    }
}
