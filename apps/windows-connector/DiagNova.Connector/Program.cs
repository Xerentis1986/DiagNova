using DiagNova.Connector.Adapters;
using DiagNova.Connector.Auth;

var builder = WebApplication.CreateBuilder(args);

// Nur Loopback – keine offenen Netzwerk-Endpunkte.
builder.WebHost.UseUrls("http://127.0.0.1:8765");

builder.Services.AddSingleton<IDiagnosticAdapter, StubDiagnosticAdapter>();
builder.Services.AddSingleton<LocalAuthService>();

var app = builder.Build();

app.Use(async (ctx, next) =>
{
    var auth = ctx.RequestServices.GetRequiredService<LocalAuthService>();
    if (!auth.IsAuthorized(ctx.Request))
    {
        ctx.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await ctx.Response.WriteAsJsonAsync(new
        {
            error = "unauthorized",
            message_de = "Localhost-Auth erforderlich. Siehe docs/windows-connector-auth.md"
        });
        return;
    }
    await next();
});

app.MapGet("/health", (IDiagnosticAdapter adapter) => Results.Json(new
{
    status = "ok",
    adapter = adapter.Name,
    data_source = "simulated",
    message_de = "Connector-Skelett – keine echten Fahrzeugbefehle."
}));

app.MapGet("/status", (IDiagnosticAdapter adapter) => Results.Json(adapter.GetStatus()));

app.Run();
