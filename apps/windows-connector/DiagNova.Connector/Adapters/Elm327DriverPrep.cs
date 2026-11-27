using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;

namespace DiagNova.Connector.Adapters;

/// <summary>
/// ELM327 / Vgate-Treiber-Vorbereitung: nur dokumentierte AT-Initialisierungssequenzen
/// über <see cref="ISerialTransport"/>. Keine Mode-01/03/04-Fahrzeugbefehle.
/// Vgate vLinker MC+ Windows-SPP-Variante muss vor Hardwarefreigabe verifiziert werden.
/// </summary>
public sealed class Elm327DriverPrep
{
    /// <summary>Nur Adapter-AT-Init – keine OBD-Service-Requests.</summary>
    public static readonly string[] SafeAtInitSequence =
    {
        "ATZ",
        "ATE0",
        "ATL0",
        "ATH0",
        "ATI"
    };

    private readonly DiagnosticProtocolLog _log;

    public Elm327DriverPrep(DiagnosticProtocolLog log)
    {
        _log = log;
    }

    public async Task<Elm327PrepResult> RunAtInitAsync(
        ISerialTransport transport,
        TimeSpan commandTimeout,
        CancellationToken cancellationToken = default)
    {
        if (!transport.IsOpen)
        {
            throw new InvalidOperationException("Transport muss vor AT-Init geöffnet sein.");
        }

        var responses = new List<Elm327AtExchange>();
        foreach (var cmd in SafeAtInitSequence)
        {
            cancellationToken.ThrowIfCancellationRequested();
            _log.Info("elm327-prep", $"AT-Init: {cmd}");
            var raw = await transport.TransactTextAsync(cmd, commandTimeout, cancellationToken)
                .ConfigureAwait(false);
            var ok = LooksLikeAtSuccess(cmd, raw);
            responses.Add(new Elm327AtExchange(cmd, raw, ok));
            _log.Info("elm327-prep", ok ? $"AT OK: {cmd}" : $"AT unklar: {cmd}", Truncate(raw));
            if (!ok && cmd == "ATZ")
            {
                return new Elm327PrepResult(false, responses, "ATZ fehlgeschlagen – Adapter nicht erreichbar oder kein ELM-kompatibles Gerät.");
            }
        }

        var allOk = responses.All(r => r.Success);
        return new Elm327PrepResult(
            allOk,
            responses,
            allOk
                ? "AT-Init (Vorbereitung) erfolgreich – keine Fahrzeugbefehle gesendet."
                : "AT-Init teilweise fehlgeschlagen – siehe Exchanges."
        );
    }

    /// <summary>
    /// Blockiert bewusst OBD-Rohbefehle (z. B. "0100", "03", "04") in Phase 03.
    /// </summary>
    public static bool IsVehicleObdCommand(string command)
    {
        var c = command.Trim().ToUpperInvariant();
        if (c.StartsWith("AT", StringComparison.Ordinal)) return false;
        // Hex-Service-Request ohne AT-Prefix
        return c.Length >= 2 && c.All(ch => Uri.IsHexDigit(ch) || char.IsWhiteSpace(ch));
    }

    public Task RejectVehicleCommandAsync(string command)
    {
        if (IsVehicleObdCommand(command))
        {
            _log.Warn("elm327-prep", "Fahrzeugbefehl in Phase 03 blockiert", command);
            throw new InvalidOperationException(
                "Phase 03 erlaubt keine OBD-/Fahrzeugbefehle. Nur AT-Init-Vorbereitung.");
        }
        return Task.CompletedTask;
    }

    private static bool LooksLikeAtSuccess(string cmd, string raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return false;
        if (raw.Contains('?') && !raw.Contains("OK", StringComparison.OrdinalIgnoreCase) &&
            !raw.Contains("ELM", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        if (cmd.Equals("ATZ", StringComparison.OrdinalIgnoreCase) ||
            cmd.Equals("ATI", StringComparison.OrdinalIgnoreCase))
        {
            return raw.Contains("ELM", StringComparison.OrdinalIgnoreCase) ||
                   raw.Contains('>');
        }
        return raw.Contains("OK", StringComparison.OrdinalIgnoreCase) || raw.Contains('>');
    }

    private static string Truncate(string s) =>
        s.Length <= 120 ? s : s[..120] + "…";
}

public sealed record Elm327AtExchange(string Command, string RawResponse, bool Success);

public sealed record Elm327PrepResult(
    bool Success,
    IReadOnlyList<Elm327AtExchange> Exchanges,
    string MessageDe
);
