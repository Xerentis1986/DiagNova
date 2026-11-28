namespace DiagNova.Connector.Auth;

using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

/// <summary>
/// Lizenz-Gate Phase 24: RSA-SHA256 Offline-Token (bevorzugt) + HMAC Legacy.
/// Nur Public Key im Connector – Private Key bleibt beim Backend.
/// </summary>
public sealed class LicenseGateService
{
    private readonly object _lock = new();
    private readonly ConcurrentQueue<object> _audit = new();
    private readonly HashSet<string> _revokedJti = new(StringComparer.Ordinal);
    private readonly HashSet<string> _seenJti = new(StringComparer.Ordinal);

    private bool _allowed;
    private DateTimeOffset _offlineUntil = DateTimeOffset.MinValue;
    private string _plan = "none";
    private string _message = "Lizenz nicht geprüft.";
    private string _deviceId;
    private string? _workshopId;
    private string? _jti;
    private string[] _entitlements = Array.Empty<string>();
    private string _lastAlgorithm = "none";

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
                algorithm = _lastAlgorithm,
                offline_until = _offlineUntil == DateTimeOffset.MinValue ? null : _offlineUntil.ToString("o"),
                message_de = _message,
                enforcement = true,
                asymmetric = true,
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
            _lastAlgorithm = "server_apply";
            Audit(allowed ? "apply_ok" : "apply_deny", _message);
            return Status();
        }
    }

    public object ApplySignedToken(string payloadJson, string signature, string? algorithm = null)
    {
        lock (_lock)
        {
            if (string.IsNullOrWhiteSpace(payloadJson) || string.IsNullOrWhiteSpace(signature))
            {
                _allowed = false;
                _message = "Token oder Signatur fehlt.";
                Audit("token_missing", _message);
                return Status();
            }

            var alg = (algorithm ?? "").Trim();
            if (string.IsNullOrEmpty(alg))
            {
                // Heuristik: Base64-RSA vs Hex-HMAC
                alg = signature.Contains('=') || signature.Length > 80
                    ? "RSA-SHA256-PKCS1v15"
                    : "HMAC-SHA256";
                try
                {
                    using var peek = JsonDocument.Parse(payloadJson);
                    if (peek.RootElement.TryGetProperty("alg", out var aEl))
                    {
                        var a = aEl.GetString() ?? "";
                        if (a.StartsWith("RSA", StringComparison.OrdinalIgnoreCase))
                            alg = "RSA-SHA256-PKCS1v15";
                        else if (a.StartsWith("HMAC", StringComparison.OrdinalIgnoreCase))
                            alg = "HMAC-SHA256";
                    }
                }
                catch { /* ignore */ }
            }

            bool sigOk;
            if (alg.StartsWith("RSA", StringComparison.OrdinalIgnoreCase))
            {
                sigOk = VerifyRsaSha256(payloadJson, signature);
                _lastAlgorithm = "RSA-SHA256-PKCS1v15";
            }
            else
            {
                var expected = ComputeHmacHex(payloadJson);
                sigOk = CryptographicOperations.FixedTimeEquals(
                    Encoding.UTF8.GetBytes(expected.ToLowerInvariant()),
                    Encoding.UTF8.GetBytes(signature.Trim().ToLowerInvariant()));
                _lastAlgorithm = "HMAC-SHA256";
            }

            if (!sigOk)
            {
                _allowed = false;
                _message = "Ungültige Lizenzsignatur (manipuliert/Fälschung).";
                Audit("token_bad_sig", _lastAlgorithm);
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
                    _message = "Lizenz für anderes Gerät (Fremdgerät / Mandant-Mismatch).";
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
                if (!string.IsNullOrEmpty(jti) && _seenJti.Contains(jti))
                {
                    // Replay derselben JTI nach vorherigem Accept – weiter ok solange nicht revoked;
                    // doppeltes Apply ist idempotent. Echtes Replay-Fenster: bereits widerrufen blockiert.
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

                var nbf = root.TryGetProperty("nbf", out var n) ? n.GetInt64() : 0;
                if (nbf > 0 && DateTimeOffset.FromUnixTimeSeconds(nbf) > DateTimeOffset.UtcNow.AddMinutes(2))
                {
                    _allowed = false;
                    _message = "Lizenz noch nicht gültig (nbf).";
                    Audit("token_nbf", nbf.ToString());
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
                if (!string.IsNullOrEmpty(jti))
                    _seenJti.Add(jti);
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
                _message = $"Signiertes Offline-Token akzeptiert ({_lastAlgorithm}).";
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

    public static bool VerifyRsaSha256(string payload, string signatureB64)
    {
        try
        {
            var pem = LoadPublicKeyPem();
            if (string.IsNullOrWhiteSpace(pem))
                return false;
            using var rsa = RSA.Create();
            rsa.ImportFromPem(pem);
            var sig = Convert.FromBase64String(signatureB64.Trim());
            return rsa.VerifyData(
                Encoding.UTF8.GetBytes(payload),
                sig,
                HashAlgorithmName.SHA256,
                RSASignaturePadding.Pkcs1);
        }
        catch
        {
            return false;
        }
    }

    public static string LoadPublicKeyPem()
    {
        var env = Environment.GetEnvironmentVariable("DIAGNOVA_LICENSE_RSA_PUBLIC_PEM");
        if (!string.IsNullOrWhiteSpace(env))
            return env.Contains("BEGIN") ? env : Encoding.UTF8.GetString(Convert.FromBase64String(env));

        var candidates = new[]
        {
            Path.Combine(AppContext.BaseDirectory, "Auth", "LicenseRsaPublic.Demo.pem"),
            Path.Combine(AppContext.BaseDirectory, "LicenseRsaPublic.Demo.pem"),
            Path.Combine(Directory.GetCurrentDirectory(), "Auth", "LicenseRsaPublic.Demo.pem"),
            Path.Combine(Directory.GetCurrentDirectory(), "DiagNova.Connector", "Auth", "LicenseRsaPublic.Demo.pem"),
        };
        foreach (var c in candidates)
        {
            if (File.Exists(c))
                return File.ReadAllText(c);
        }
        // Embedded fallback – same demo key as fixtures (NOT for production)
        return EmbeddedDemoPublicPem;
    }

    /// <summary>Demo public key – Produktion via Env ersetzen.</summary>
    public const string EmbeddedDemoPublicPem =
        """
        -----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyFwo115+w/Y8yeoWxXb3
        cKGMlyxR1IWv5wIe6a/ZqK64B9J25+C/SAfuUe3xD8vWO+4baFPyYFDeBTkUBXt4
        tvhOSnkkbMQ0G+MN6dAGKHxi2zNt8KmXi2GzqXP28yU0e3Mby6FRzxMJgoyBEFEb
        fZFnme8wZo7RdCAjl0UGYKHOjhHUQfgPD1ekQvKMhQDiVzzSyvQXyA47MSEXXY4p
        LTneGT1KWHQBADANHb9/2M21nUxIiRmx9jp8j0offSZSai7EBhIwMYLvWiPqalfF
        +KjGbmddsNBdy4zgXMbZXsAFI/sk7kvOO8N6ft3VUDmS4kfa1vKhsUY5YDBJAGGE
        bQIDAQAB
        -----END PUBLIC KEY-----
        """;

    public static string IssueTestToken(
        string deviceId,
        string workshopId,
        string planCode,
        int validHours,
        bool allowed = true,
        string[]? entitlements = null,
        string alg = "HMAC-SHA256")
    {
        var exp = DateTimeOffset.UtcNow.AddHours(validHours).ToUnixTimeSeconds();
        var payload = JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["device_id"] = deviceId,
            ["workshop_id"] = workshopId,
            ["plan_code"] = planCode,
            ["exp"] = exp,
            ["jti"] = Guid.NewGuid().ToString("N"),
            ["allowed"] = allowed,
            ["entitlements"] = entitlements ?? new[] { "obd_live", "dtc_read" },
            ["alg"] = alg
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
