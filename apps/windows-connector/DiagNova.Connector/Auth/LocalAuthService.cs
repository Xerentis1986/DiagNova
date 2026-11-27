namespace DiagNova.Connector.Auth;

/// <summary>
/// Localhost-Auth: Bearer Session-Token (nach Pairing) oder Bootstrap-CONNECTOR_TOKEN.
/// Öffentliche Pfade: /pair/info (ohne Secrets), /pair (mit Pairing-Code).
/// </summary>
public sealed class LocalAuthService
{
    private readonly PairingService _pairing;
    private readonly OriginGuard _origin;

    private static readonly HashSet<string> PublicPaths = new(StringComparer.OrdinalIgnoreCase)
    {
        "/pair",
        "/pair/info"
    };

    public LocalAuthService(PairingService pairing, OriginGuard origin)
    {
        _pairing = pairing;
        _origin = origin;
    }

    public bool IsPublicPath(PathString path) => PublicPaths.Contains(path.Value ?? "");

    public bool IsAuthorized(HttpRequest request)
    {
        if (!_origin.IsOriginAllowed(request))
        {
            return false;
        }

        if (IsPublicPath(request.Path))
        {
            return true;
        }

        var header = request.Headers.Authorization.ToString();
        if (string.IsNullOrWhiteSpace(header) || !header.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        var provided = header["Bearer ".Length..].Trim();
        return _pairing.IsSessionValid(provided);
    }
}
