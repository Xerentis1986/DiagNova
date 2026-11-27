using System.Collections.Concurrent;
using System.Security.Cryptography;
using DiagNova.Connector.Logging;

namespace DiagNova.Connector.Obd;

/// <summary>
/// Freigabeschutz für Mode-04-Fehlerlöschung.
/// Erfordert Vorher-Bericht-Hinweis, explizite Bestätigung und Token.
/// Permanente DTCs werden nicht als löschbar versprochen.
/// </summary>
public sealed class ClearDtcGate
{
    private readonly DiagnosticProtocolLog _log;
    private readonly ConcurrentDictionary<string, ClearApproval> _approvals = new();

    public ClearDtcGate(DiagnosticProtocolLog log)
    {
        _log = log;
    }

    public object GetWarnings() => new
    {
        warnings_de = new[]
        {
            "Mode 04 löscht gespeicherte und pending DTCs sowie Freeze-Frame-Daten.",
            "Readiness-Monitore werden zurückgesetzt – Abgasuntersuchung kann betroffen sein.",
            "Permanente DTCs (Mode 0A) werden durch Mode 04 NICHT gelöscht und dürfen nicht als löschbar dargestellt werden.",
            "Vor dem Löschen einen Vorher-Bericht speichern und nach dem Löschen DTCs erneut auslesen.",
            "Nur am stehenden Fahrzeug und nach ausdrücklicher Werkstatt-Freigabe ausführen.",
            "Ohne Hardware bleibt die Ausführung deaktiviert bzw. nur im Simulator markiert."
        },
        permanent_dtcs_clearable = false,
        requires_confirmation_phrase = ClearApproval.RequiredPhrase,
        data_source_note_de = "Live und Demo/Simulator strikt getrennt kennzeichnen."
    };

    public ClearApprovalIssueResult IssueApproval(
        string confirmationPhrase,
        bool acknowledgeFreezeFrameLoss,
        bool acknowledgeReadinessReset,
        bool acknowledgePermanentRemain,
        bool preReportSaved,
        string? operatorNote)
    {
        if (!string.Equals(confirmationPhrase?.Trim(), ClearApproval.RequiredPhrase, StringComparison.Ordinal))
        {
            return new ClearApprovalIssueResult(false, null,
                $"Bestätigungsphrase muss exakt „{ClearApproval.RequiredPhrase}“ lauten.");
        }
        if (!acknowledgeFreezeFrameLoss || !acknowledgeReadinessReset || !acknowledgePermanentRemain)
        {
            return new ClearApprovalIssueResult(false, null,
                "Alle Warnhinweise (Freeze-Frame, Readiness, permanente DTCs) müssen bestätigt werden.");
        }
        if (!preReportSaved)
        {
            return new ClearApprovalIssueResult(false, null,
                "Vorher-Bericht muss als gespeichert bestätigt werden (pre_report_saved=true).");
        }

        var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(16));
        var approval = new ClearApproval(
            token,
            DateTimeOffset.UtcNow.AddMinutes(5),
            operatorNote ?? "");
        _approvals[token] = approval;
        _log.Warn("obd-clear", "Clear-DTC-Freigabe ausgestellt (5 Min)", token[..8] + "…");
        return new ClearApprovalIssueResult(true, approval,
            "Freigabe erteilt – Token innerhalb von 5 Minuten mit POST /obd/dtc/clear verwenden.");
    }

    public bool TryConsume(string token, out ClearApproval? approval, out string messageDe)
    {
        approval = null;
        if (string.IsNullOrWhiteSpace(token) || !_approvals.TryRemove(token, out var found))
        {
            messageDe = "Ungültiges oder bereits verwendetes Freigabe-Token.";
            return false;
        }
        if (found.ExpiresAt < DateTimeOffset.UtcNow)
        {
            messageDe = "Freigabe-Token abgelaufen.";
            return false;
        }
        approval = found;
        messageDe = "Freigabe verbraucht.";
        _log.Warn("obd-clear", "Clear-DTC-Freigabe verbraucht", token[..8] + "…");
        return true;
    }
}

public sealed record ClearApproval(string Token, DateTimeOffset ExpiresAt, string OperatorNote)
{
    public const string RequiredPhrase = "FEHLERCODES LOESCHEN";
}

public sealed record ClearApprovalIssueResult(bool Success, ClearApproval? Approval, string MessageDe);
