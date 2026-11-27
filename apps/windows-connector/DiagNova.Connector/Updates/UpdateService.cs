using System.Security.Cryptography;
using System.Text;

namespace DiagNova.Connector.Updates;

/// <summary>
/// Staging/Integritätsprüfung für Connector-Pakete (Simulation). Kein ungeprüftes Auto-Install.
/// </summary>
public sealed class UpdateService
{
    private readonly UpdateBusyGate _busy;
    private string _current = ConnectorVersion.Version;
    private string? _previous;
    private string _health = "ok";
    private string? _lastError;

    public UpdateService(UpdateBusyGate busy) => _busy = busy;

    public object Status() => new
    {
        component = "connector",
        version = _current,
        previous_version = _previous,
        channel = ConnectorVersion.Channel,
        health_status = _health,
        last_error_de = _lastError,
        auto_install = false,
        signing_required = true,
        note_de = ConnectorVersion.PhaseNoteDe
    };

    public object VerifyPackage(string payloadCanonical, string claimedSha256, string? signatureHex, string hmacSecret)
    {
        var body = Encoding.UTF8.GetBytes(payloadCanonical);
        var actual = Convert.ToHexString(SHA256.HashData(body)).ToLowerInvariant();
        var checksumOk = string.Equals(actual, claimedSha256?.Trim(), StringComparison.OrdinalIgnoreCase);

        bool? signatureOk = null;
        if (!string.IsNullOrWhiteSpace(signatureHex))
        {
            using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(hmacSecret));
            var expected = Convert.ToHexString(hmac.ComputeHash(body)).ToLowerInvariant();
            signatureOk = string.Equals(expected, signatureHex.Trim(), StringComparison.OrdinalIgnoreCase);
        }

        var ok = checksumOk && signatureOk != false;
        return new
        {
            ok,
            checksum_ok = checksumOk,
            signature_ok = signatureOk,
            actual_sha256 = actual,
            message_de = ok
                ? "Integrität OK (Simulation)."
                : "Paket abgelehnt: Checksum/Signatur ungültig."
        };
    }

    public object TryStageInstall(string targetVersion, bool adminApproved)
    {
        var busy = _busy.Snapshot();
        if (!busy.Allowed)
        {
            return new
            {
                status = "blocked_busy",
                reason_de = busy.ReasonDe,
                blockers = busy.Blockers
            };
        }

        if (!adminApproved)
        {
            return new
            {
                status = "awaiting_approval",
                message_de = "Admin-Freigabe erforderlich. Keine ungeprüften Auto-Installs."
            };
        }

        _previous = _current;
        _current = targetVersion;
        _health = "ok";
        _lastError = null;
        return new
        {
            status = "succeeded",
            from_version = _previous,
            to_version = _current,
            healthcheck_ok = true,
            message_de = "Atomare Installation simuliert (Healthcheck OK)."
        };
    }

    public object Rollback()
    {
        var busy = _busy.Snapshot();
        if (!busy.Allowed)
        {
            return new { status = "blocked_busy", reason_de = busy.ReasonDe };
        }

        if (string.IsNullOrEmpty(_previous))
        {
            return new { status = "failed", error_de = "Kein vorheriger Stand." };
        }

        var from = _current;
        _current = _previous;
        _previous = from;
        return new
        {
            status = "succeeded",
            from_version = from,
            to_version = _current,
            message_de = "Rollback simuliert."
        };
    }
}
