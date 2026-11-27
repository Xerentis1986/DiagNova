namespace DiagNova.Connector.Updates;

/// <summary>
/// Sperrt lokale Connector-Updates während Diagnose/Service/Flash-ähnlicher Aktivität.
/// </summary>
public sealed class UpdateBusyGate
{
    private int _diagnosisSessions;
    private int _serviceOps;
    private int _flashOps;
    private readonly object _lock = new();

    public void BeginDiagnosis() { lock (_lock) { _diagnosisSessions++; } }
    public void EndDiagnosis() { lock (_lock) { if (_diagnosisSessions > 0) _diagnosisSessions--; } }

    public void BeginService() { lock (_lock) { _serviceOps++; } }
    public void EndService() { lock (_lock) { if (_serviceOps > 0) _serviceOps--; } }

    public void BeginFlash() { lock (_lock) { _flashOps++; } }
    public void EndFlash() { lock (_lock) { if (_flashOps > 0) _flashOps--; } }

    public UpdateBusyStatus Snapshot()
    {
        lock (_lock)
        {
            var blockers = new List<object>();
            if (_diagnosisSessions > 0)
                blockers.Add(new { kind = "diagnosis", count = _diagnosisSessions, detail_de = "Diagnosesitzung aktiv." });
            if (_serviceOps > 0)
                blockers.Add(new { kind = "service", count = _serviceOps, detail_de = "Serviceoperation aktiv." });
            if (_flashOps > 0)
                blockers.Add(new { kind = "coding_flash", count = _flashOps, detail_de = "Flash/Codierung aktiv." });

            var allowed = blockers.Count == 0;
            return new UpdateBusyStatus(
                allowed,
                allowed
                    ? null
                    : "Update gesperrt: aktive Diagnose/Service/Flash. Keine Installation während laufender Ops.",
                blockers
            );
        }
    }
}

public sealed record UpdateBusyStatus(bool Allowed, string? ReasonDe, IReadOnlyList<object> Blockers);
