namespace DiagNova.Connector.Auth;

/// <summary>
/// Prüft Origin/Referer gegen Allowlist. Nur Loopback-Origins standardmäßig.
/// </summary>
public sealed class OriginGuard
{
    private readonly HashSet<string> _allowed;

    public OriginGuard(IConfiguration config)
    {
        var configured = config["CONNECTOR_ALLOWED_ORIGINS"]
            ?? Environment.GetEnvironmentVariable("CONNECTOR_ALLOWED_ORIGINS");

        var defaults = new[]
        {
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:3000",
            "http://localhost:3000"
        };

        _allowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var o in defaults) _allowed.Add(o);

        if (!string.IsNullOrWhiteSpace(configured))
        {
            foreach (var part in configured.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            {
                _allowed.Add(part);
            }
        }
    }

    public IReadOnlyCollection<string> AllowedOrigins => _allowed;

    public bool IsOriginAllowed(HttpRequest request)
    {
        // Nicht-Browser-Clients (curl, Tests) ohne Origin/Referer: erlaubt, da Loopback-Bindung Pflicht ist.
        if (!request.Headers.ContainsKey("Origin") && !request.Headers.ContainsKey("Referer"))
        {
            return true;
        }

        if (request.Headers.TryGetValue("Origin", out var origin) && !string.IsNullOrWhiteSpace(origin))
        {
            return _allowed.Contains(origin.ToString());
        }

        if (request.Headers.TryGetValue("Referer", out var referer) && Uri.TryCreate(referer.ToString(), UriKind.Absolute, out var uri))
        {
            var originFromReferer = $"{uri.Scheme}://{uri.Authority}";
            return _allowed.Contains(originFromReferer);
        }

        return false;
    }
}
