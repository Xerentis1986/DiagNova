namespace DiagNova.Connector.Auth;

/// <summary>
/// Lizenz-Gate vor Diagnosebefehlen. Offline-Cache zeitlich begrenzt (HMAC lokal).
/// Ohne gültige Lizenz: OBD gesperrt (außer explizitem Demo/Simulator-Pfad).
/// </summary>
public sealed class LicenseGateService
{
    private readonly object _lock = new();
    private bool _allowed;
    private DateTimeOffset _offlineUntil = DateTimeOffset.MinValue;
    private string _plan = "none";
    private string _message = "Lizenz nicht geprüft.";

    public object Status() => new
    {
        allowed = IsAllowed(),
        plan_code = _plan,
        offline_until = _offlineUntil == DateTimeOffset.MinValue ? null : _offlineUntil.ToString("o"),
        message_de = _message,
        enforcement = true
    };

    public bool IsAllowed()
    {
        lock (_lock)
        {
            if (_allowed && DateTimeOffset.UtcNow <= _offlineUntil)
                return true;
            if (_allowed && DateTimeOffset.UtcNow > _offlineUntil)
            {
                _allowed = false;
                _message = "Offline-Lizenzfenster abgelaufen – erneut am Backend verifizieren.";
            }
            return _allowed;
        }
    }

    public object ApplyServerVerification(bool allowed, string planCode, int offlineHours, string? messageDe)
    {
        lock (_lock)
        {
            _allowed = allowed;
            _plan = planCode;
            _offlineUntil = allowed
                ? DateTimeOffset.UtcNow.AddHours(Math.Clamp(offlineHours, 1, 72))
                : DateTimeOffset.MinValue;
            _message = messageDe
                ?? (allowed ? "Lizenz aktiv (Connector-Gate)." : "Lizenz verweigert.");
            return Status();
        }
    }

    public object Deny(string reasonDe)
    {
        lock (_lock)
        {
            _allowed = false;
            _message = reasonDe;
            _offlineUntil = DateTimeOffset.MinValue;
            return Status();
        }
    }
}
