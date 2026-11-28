namespace DiagNova.Connector.Auth;

using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

/// <summary>
/// Volles Lizenz-Gate: Gerätebindung, HMAC-Offline-Token, Entitlements, Ablauf, Widerruf, Audit.
/// DEMO/Simulator/Fake-Adapter ohne Paid-Lizenz erlaubt (Produktmodell). Live-Hardware braucht Gate.
/// </summary>
public sealed class LicenseGateService
{
    private readonly object _lock = new();
    private readonly ConcurrentQueue<object> _audit = new();
    private readonly HashSet<string> _revokedJti = new(StringComparer.Ordinal);

    private bool _allowed;
    private DateTimeOffset _offlineUntil = DateTimeOffset.MinValue;
    private string _plan = "none";
    private string _message = "Lizenz nicht geprüft.";
    private string _deviceId;
    private string? _workshopId;
    private string? _jti;
    private string[] _entitlements = Array.Empty<string>();

    /// <summary>HMAC-Demo-Secret – Produktion ersetzt via Env DIAGNOVA_LICENSE_HMAC_SECRET.</summary>
    public static string HmacSecret =>
        Environment.GetEnvironmentVariable("DIAGNOVA_LICENSE_HMAC_SECRET")
        ?? "diagnova-phase23-license-hmac-not-for-prod";

    public LicenseGateService()
    {
        _deviceId = ResolveDeviceId();
    }

    public string DeviceId => _deviceId;

    public static string ResolveDeviceId()
    {
        var env = Environment.GetEnvironmentVariable("DIAGNOVA_DEVICE_ID");
        if (!string.IsNullOrWhiteSpace(env))
            return env.Trim();
        var machine = Environment.MachineName ?? "unknown";
        var user = Environment.UserName ?? "user";
        var raw = $"diagnova|{machine}|{user}|{Environment.OSVersion}";
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
        return "dev_" + Convert.ToHexString(hash)[..16].ToLowerInvariant();
    }

    public object Status()
    {
        lock (_lock)
        {
            return new
            {
                allowed = IsAllowedUnlocked(),
                plan_code = _plan,
                device_id = _deviceId,
                workshop_id = _workshopId,
                jti = _jti,
                entitlements = _entitlements,
                offline_until = _offlineUntil == DateTimeOffset.MinValue ? null : _offlineUntil.ToString("o"),
                message_de = _message,
                enforcement = true,
                revoked_count = _revokedJti.Count,
                audit_tail = _audit.Reverse().Take(10).ToArray()
            };
        }
    }

    public bool IsAllowed()
    {
        lock (_lock)
            return IsAllowedUnlocked();
    }

    private bool IsAllowedUnlocked()
    {
        if (_jti is not null && _revokedJti.Contains(_jti))
        {
            _allowed = false;
            _message = "Lizenz widerrufen (JTI).";
            return false;
        }
        if (_allowed && DateTimeOffset.UtcNow <= _offlineUntil)
            return true;
        if (_allowed && DateTimeOffset.UtcNow > _offlineUntil)
        {
            _allowed = false;
            _message = "Offline-Lizenzfenster abgelaufen – erneut am Backend verifizieren.";
            Audit("expired", _message);
        }
        return _allowed;
    }

    public bool AllowsDemoPath(bool isDemoOrSimulatorOrFake) => isDemoOrSimulatorOrFake;

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
            _jti = allowed ? Guid.NewGuid().ToString("N") : null;
            _entitlements = allowed ? new[] { "obd_live", "dtc_read" } : Array.Empty<string>();
            Audit(allowed ? "apply_ok" : "apply_deny", _message);
            return Status();
        }
    }

    /// <summary>
    /// Wendet signiertes Offline-Token an.
    /// Payload JSON: device_id, workshop_id, plan_code, exp (unix), jti, entitlements[], allowed
    /// Signatur: hex HMAC-SHA256 über UTF8(payload).
    /// </summary>
    public object ApplySignedToken(string payloadJson, string signatureHex)
    {
        lock (_lock)
        {
            if (string.IsNullOrWhiteSpace(payloadJson) || string.IsNullOrWhiteSpace(signatureHex))
            {
                _allowed = false;
                _message = "Token oder Signatur fehlt.";
                Audit("token_missing", _message);
                return Status();
            }

            var expected = ComputeHmacHex(payloadJson);
            if (!CryptographicOperations.FixedTimeEquals(
                    Encoding.UTF8.GetBytes(expected.ToLowerInvariant()),
                    Encoding.UTF8.GetBytes(signatureHex.Trim().ToLowerInvariant())))
            {
                _allowed = false;
                _message = "Ungültige Lizenzsignatur (manipuliert).";
                Audit("token_bad_sig", _message);
                return Status();
            }

            try
            {
                using var doc = JsonDocument.Parse(payloadJson);
                var root = doc.RootElement;
                var device = root.TryGetProperty("device_id", out var d) ? d.GetString() ?? "" : "";
                if (!string.Equals(device, _deviceId, StringComparison.Ordinal))
                {
                    _allowed = false;
                    _message = "Lizenz für anderes Gerät (Fremdgerät).";
                    Audit("token_foreign_device", $"token={device} local={_deviceId}");
                    return Status();
                }

                var jti = root.TryGetProperty("jti", out var j) ? j.GetString() : null;
                if (!string.IsNullOrEmpty(jti) && _revokedJti.Contains(jti))
                {
                    _allowed = false;
                    _jti = jti;
                    _message = "Lizenz widerrufen.";
                    Audit("token_revoked", jti);
                    return Status();
                }

                var exp = root.TryGetProperty("exp", out var e) ? e.GetInt64() : 0;
                var expDt = DateTimeOffset.FromUnixTimeSeconds(exp);
                if (expDt <= DateTimeOffset.UtcNow)
                {
                    _allowed = false;
                    _message = "Lizenz abgelaufen.";
                    Audit("token_expired", expDt.ToString("o"));
                    return Status();
                }

                var allowed = !root.TryGetProperty("allowed", out var a) || a.GetBoolean();
                if (!allowed)
                {
                    _allowed = false;
                    _message = "Lizenz verweigert (allowed=false).";
                    Audit("token_denied", _message);
                    return Status();
                }

                _allowed = true;
                _plan = root.TryGetProperty("plan_code", out var p) ? p.GetString() ?? "licensed" : "licensed";
                _workshopId = root.TryGetProperty("workshop_id", out var w) ? w.GetString() : null;
                _jti = jti;
                _offlineUntil = expDt;
                if (root.TryGetProperty("entitlements", out var ent) && ent.ValueKind == JsonValueKind.Array)
                {
                    _entitlements = ent.EnumerateArray()
                        .Select(x => x.GetString() ?? "")
                        .Where(x => x.Length > 0)
                        .ToArray();
                }
                else
                {
                    _entitlements = new[] { "obd_live", "dtc_read" };
                }
                _message = "Signiertes Offline-Token akzeptiert.";
                Audit("token_ok", _jti ?? "");
                return Status();
            }
            catch (Exception ex)
            {
                _allowed = false;
                _message = "Token-Payload ungültig: " + ex.Message;
                Audit("token_parse_error", ex.Message);
                return Status();
            }
        }
    }

    public object Revoke(string? jti = null)
    {
        lock (_lock)
        {
            var id = jti ?? _jti;
            if (!string.IsNullOrEmpty(id))
                _revokedJti.Add(id);
            _allowed = false;
            _message = "Lizenz widerrufen.";
            _offlineUntil = DateTimeOffset.MinValue;
            Audit("revoke", id ?? "all_local");
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
            Audit("deny", reasonDe);
            return Status();
        }
    }

    public static string ComputeHmacHex(string payload)
    {
        var key = Encoding.UTF8.GetBytes(HmacSecret);
        var mac = HMACSHA256.HashData(key, Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(mac).ToLowerInvariant();
    }

    public static string IssueTestToken(
        string deviceId,
        string workshopId,
        string planCode,
        int validHours,
        bool allowed = true,
        string[]? entitlements = null)
    {
        var exp = DateTimeOffset.UtcNow.AddHours(validHours).ToUnixTimeSeconds();
        var payload = JsonSerializer.Serialize(new
        {
            device_id = deviceId,
            workshop_id = workshopId,
            plan_code = planCode,
            exp,
            jti = Guid.NewGuid().ToString("N"),
            allowed,
            entitlements = entitlements ?? new[] { "obd_live", "dtc_read" }
        });
        return payload;
    }

    private void Audit(string kind, string detail)
    {
        _audit.Enqueue(new
        {
            at = DateTimeOffset.UtcNow.ToString("o"),
            kind,
            detail
        });
        while (_audit.Count > 100 && _audit.TryDequeue(out _)) { }
    }
}
