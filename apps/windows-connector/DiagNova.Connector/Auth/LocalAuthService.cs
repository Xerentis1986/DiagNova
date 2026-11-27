namespace DiagNova.Connector.Auth;

/// <summary>
/// Minimaler Localhost-Auth-Hinweis: erwartet Bearer-Token aus Umgebungsvariable.
/// Produktion: Pairing + DPAPI, siehe docs/windows-connector-auth.md.
/// </summary>
public sealed class LocalAuthService
{
    private readonly string _token;

    public LocalAuthService(IConfiguration config)
    {
        _token = config["CONNECTOR_TOKEN"]
            ?? Environment.GetEnvironmentVariable("CONNECTOR_TOKEN")
            ?? "dev-only-change-me";
    }

    public bool IsAuthorized(HttpRequest request)
    {
        var header = request.Headers.Authorization.ToString();
        if (string.IsNullOrWhiteSpace(header) || !header.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }
        var provided = header["Bearer ".Length..].Trim();
        return CryptographicEquals(provided, _token);
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
