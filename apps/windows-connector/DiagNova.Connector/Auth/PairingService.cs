using System.Collections.Concurrent;
using System.Security.Cryptography;

namespace DiagNova.Connector.Auth;

public sealed record PairingInfo(
    string PairingCode,
    DateTimeOffset PairingExpiresAt,
    string MessageDe
);

public sealed record SessionTokenInfo(
    string Token,
    DateTimeOffset ExpiresAt
);

/// <summary>
/// Kurzlebige Pairing-Codes und Session-Tokens für Browser↔Connector-Kopplung.
/// </summary>
public sealed class PairingService
{
    private readonly object _gate = new();
    private string _pairingCode = "000000";
    private DateTimeOffset _pairingExpires;
    private readonly ConcurrentDictionary<string, DateTimeOffset> _sessions = new();
    private readonly TimeSpan _pairingTtl;
    private readonly TimeSpan _sessionTtl;
    private readonly string? _bootstrapToken;

    public PairingService(IConfiguration config)
    {
        _pairingTtl = TimeSpan.FromMinutes(
            int.TryParse(config["CONNECTOR_PAIRING_TTL_MINUTES"], out var p) ? Math.Clamp(p, 1, 30) : 10);
        _sessionTtl = TimeSpan.FromMinutes(
            int.TryParse(config["CONNECTOR_SESSION_TTL_MINUTES"], out var s) ? Math.Clamp(s, 5, 24 * 60) : 120);

        _bootstrapToken = config["CONNECTOR_TOKEN"]
            ?? Environment.GetEnvironmentVariable("CONNECTOR_TOKEN");

        RotatePairingCode();
    }

    public PairingInfo GetPairingInfo()
    {
        lock (_gate)
        {
            if (DateTimeOffset.UtcNow >= _pairingExpires)
            {
                RotatePairingCode();
            }
            return new PairingInfo(
                _pairingCode,
                _pairingExpires,
                "Pairing-Code lokal im Connector anzeigen und in der Web-App eingeben. Nur Loopback."
            );
        }
    }

    public void RotatePairingCode()
    {
        lock (_gate)
        {
            _pairingCode = RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");
            _pairingExpires = DateTimeOffset.UtcNow.Add(_pairingTtl);
        }
    }

    public bool TryPair(string pairingCode, out SessionTokenInfo? session)
    {
        session = null;
        lock (_gate)
        {
            if (DateTimeOffset.UtcNow >= _pairingExpires)
            {
                RotatePairingCode();
                return false;
            }
            if (!CryptographicEquals(pairingCode.Trim(), _pairingCode))
            {
                return false;
            }
            // Einmal-Code: nach erfolgreichem Pairing rotieren
            RotatePairingCode();
        }

        session = IssueSession();
        return true;
    }

    public SessionTokenInfo IssueSession()
    {
        var token = Convert.ToBase64String(RandomNumberGenerator.GetBytes(32));
        var expires = DateTimeOffset.UtcNow.Add(_sessionTtl);
        _sessions[token] = expires;
        CleanupExpired();
        return new SessionTokenInfo(token, expires);
    }

    public bool IsSessionValid(string token)
    {
        if (_bootstrapToken is not null &&
            CryptographicEquals(token, _bootstrapToken))
        {
            return true;
        }

        if (_sessions.TryGetValue(token, out var expires))
        {
            if (DateTimeOffset.UtcNow <= expires)
            {
                return true;
            }
            _sessions.TryRemove(token, out _);
        }
        return false;
    }

    private void CleanupExpired()
    {
        var now = DateTimeOffset.UtcNow;
        foreach (var kv in _sessions)
        {
            if (kv.Value < now)
            {
                _sessions.TryRemove(kv.Key, out _);
            }
        }
    }

    private static bool CryptographicEquals(string a, string b)
    {
        if (a.Length != b.Length) return false;
        var result = 0;
        for (var i = 0; i < a.Length; i++)
        {
            result |= a[i] ^ b[i];
        }
        return result == 0;
    }
}
