using System.Net;
using System.Runtime.InteropServices;
using DiagNova.Connector.Adapters;
using DiagNova.Connector.Auth;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;

var builder = WebApplication.CreateBuilder(args);

// Nur Loopback – keine offenen Netzwerk-Endpunkte.
const string loopbackUrl = "http://127.0.0.1:8765";
builder.WebHost.UseUrls(loopbackUrl);

builder.Services.AddSingleton<DiagnosticProtocolLog>();
builder.Services.AddSingleton<IComPortScanner, ComPortScanner>();
builder.Services.AddSingleton<IBluetoothScanner, BluetoothScanner>();
builder.Services.AddSingleton<IUsbScanner, UsbScanner>();
builder.Services.AddSingleton<IDeviceInventory, CompositeDeviceInventory>();
builder.Services.AddSingleton<ISerialTransportFactory, SerialTransportFactory>();
builder.Services.AddSingleton<Elm327DriverPrep>();
builder.Services.AddSingleton<AdapterConnectionManager>();
builder.Services.AddSingleton<IDiagnosticAdapter>(sp => sp.GetRequiredService<AdapterConnectionManager>());
builder.Services.AddSingleton<PairingService>();
builder.Services.AddSingleton<OriginGuard>();
builder.Services.AddSingleton<LocalAuthService>();

var app = builder.Build();
var log = app.Services.GetRequiredService<DiagnosticProtocolLog>();
var pairing = app.Services.GetRequiredService<PairingService>();

log.Info("startup", "DiagNova Connector Phase 03 startet", loopbackUrl);
log.Info("startup", "Pairing-Code erzeugt", pairing.GetPairingInfo().PairingCode);
Console.WriteLine($"DiagNova Connector – Loopback {loopbackUrl}");
Console.WriteLine($"Pairing-Code: {pairing.GetPairingInfo().PairingCode} (gilt bis {pairing.GetPairingInfo().PairingExpiresAt:u})");
Console.WriteLine("Keine Fahrzeugbefehle in Phase 03.");

app.Use(async (ctx, next) =>
{
    // Zusätzliche Absicherung: RemoteIP muss Loopback sein.
    var remote = ctx.Connection.RemoteIpAddress;
    if (remote is not null && !IPAddress.IsLoopback(remote))
    {
        ctx.Response.StatusCode = StatusCodes.Status403Forbidden;
        await ctx.Response.WriteAsJsonAsync(new
        {
            error = "forbidden",
            message_de = "Nur Loopback-Verbindungen erlaubt."
        });
        return;
    }

    var auth = ctx.RequestServices.GetRequiredService<LocalAuthService>();
    var origin = ctx.RequestServices.GetRequiredService<OriginGuard>();
    if (!origin.IsOriginAllowed(ctx.Request))
    {
        ctx.Response.StatusCode = StatusCodes.Status403Forbidden;
        await ctx.Response.WriteAsJsonAsync(new
        {
            error = "origin_denied",
            message_de = "Origin nicht in Allowlist. Siehe CONNECTOR_ALLOWED_ORIGINS."
        });
        return;
    }

    if (!auth.IsAuthorized(ctx.Request))
    {
        ctx.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await ctx.Response.WriteAsJsonAsync(new
        {
            error = "unauthorized",
            message_de = "Localhost-Auth erforderlich. Pairing unter POST /pair oder CONNECTOR_TOKEN."
        });
        return;
    }
    await next();
});

app.MapGet("/pair/info", (PairingService pairingSvc, OriginGuard origins) =>
{
    var info = pairingSvc.GetPairingInfo();
    return Results.Json(new
    {
        pairing_expires_at = info.PairingExpiresAt,
        message_de = info.MessageDe,
        // Code wird lokal angezeigt (Console); API liefert ihn nur auf Loopback zur Workstation-UI.
        pairing_code = info.PairingCode,
        loopback = loopbackUrl,
        allowed_origins = origins.AllowedOrigins,
        note_de = "Kurzlebiges Pairing – nach Erfolg wird der Code rotiert."
    });
});

app.MapPost("/pair", async (HttpRequest req, PairingService pairingSvc, DiagnosticProtocolLog protocolLog) =>
{
    var body = await req.ReadFromJsonAsync<PairRequest>();
    if (body is null || string.IsNullOrWhiteSpace(body.PairingCode))
    {
        return Results.BadRequest(new { error = "pairing_code_required" });
    }

    if (!pairingSvc.TryPair(body.PairingCode, out var session) || session is null)
    {
        protocolLog.Warn("auth", "Pairing fehlgeschlagen");
        return Results.Json(new { error = "invalid_or_expired_pairing_code" }, statusCode: 401);
    }

    protocolLog.Info("auth", "Browser gepaart", session.ExpiresAt.ToString("u"));
    return Results.Json(new
    {
        token = session.Token,
        expires_at = session.ExpiresAt,
        token_type = "Bearer",
        message_de = "Session-Token für Connector-API. Nur über Loopback verwenden."
    });
});

app.MapGet("/health", (IDiagnosticAdapter adapter) => Results.Json(new
{
    status = "ok",
    phase = 3,
    adapter = adapter.Name,
    data_source = adapter.DataSource,
    is_simulator = adapter.IsSimulator,
    platform = RuntimeInformation.OSDescription,
    message_de = "Connector Phase 03 – Geräteerkennung/Transport, keine echten Fahrzeugbefehle."
}));

app.MapGet("/status", (AdapterConnectionManager manager) => Results.Json(manager.GetExtendedStatus()));

app.MapGet("/devices", async (IDeviceInventory inventory, CancellationToken ct) =>
{
    var snap = await inventory.ScanAsync(ct);
    return Results.Json(snap);
});

app.MapGet("/devices/com", (IComPortScanner com) => Results.Json(new { devices = com.ListComPorts() }));

app.MapGet("/devices/usb", (IUsbScanner usb) => Results.Json(new
{
    devices = usb.ListUsbDevices(),
    limitation_de = usb.LimitationDe
}));

app.MapGet("/devices/bluetooth", async (IBluetoothScanner bt, CancellationToken ct) =>
{
    var devices = await bt.ListPairedAsync(ct);
    return Results.Json(new { devices, limitation_de = bt.LimitationDe });
});

app.MapGet("/log", (DiagnosticProtocolLog protocolLog, int? limit) =>
    Results.Json(new { entries = protocolLog.Snapshot(limit ?? 100) }));

app.MapPost("/adapter/simulator", async (AdapterConnectionManager manager, CancellationToken ct) =>
    Results.Json(await manager.SelectSimulatorAsync(ct)));

app.MapPost("/adapter/connect/fake", async (AdapterConnectionManager manager, CancellationToken ct) =>
    Results.Json(await manager.ConnectFakeAsync(ct)));

app.MapPost("/adapter/connect/com", async (ConnectComRequest body, AdapterConnectionManager manager, CancellationToken ct) =>
{
    if (body is null || string.IsNullOrWhiteSpace(body.PortName))
    {
        return Results.BadRequest(new { error = "port_name_required" });
    }
    // run_at_init nur für Fake-Transport in Phase 03
    var kind = string.IsNullOrWhiteSpace(body.Transport) ? "system" : body.Transport!;
    try
    {
        var result = await manager.ConnectComAsync(body.PortName, kind, body.RunAtInit, ct);
        return Results.Json(result);
    }
    catch (Exception ex)
    {
        log.Error("connection", "COM-Connect fehlgeschlagen", ex.Message);
        return Results.Json(new { error = "connect_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapPost("/adapter/disconnect", async (AdapterConnectionManager manager, CancellationToken ct) =>
    Results.Json(await manager.DisconnectAsync(ct)));

app.MapGet("/capabilities", () => Results.Json(new
{
    phase = 3,
    vehicle_commands = false,
    features = new
    {
        device_discovery = true,
        bluetooth_paired_list = true,
        com_usb_inventory = true,
        connection_status_separated = true,
        diagnostic_protocol_log = true,
        elm327_at_prep = true,
        fake_port_tests = true,
        simulator_separate = true,
        browser_pairing = true,
        loopback_only = true,
        origin_guard = true
    },
    adapters = new object[]
    {
        new { id = "simulator", status = "available", note_de = "Separater Simulator-Pfad" },
        new { id = "elm327-prep", status = "prepared", note_de = "AT-Init über Fake/Serial – keine OBD-Services" },
        new { id = "vgate-vlinker-mc-plus", status = "blocked", note_de = "Windows-SPP-Variante und Herstellerdokumentation nicht verifiziert (BLK-ADAPTER)" },
        new { id = "delphi-autocom", status = "blocked", note_de = "Keine dokumentierte öffentliche Schnittstelle – siehe docs/delphi-autocom-interface.md" }
    },
    limitations_de = new[]
    {
        "Keine OBD-/Fahrzeugbefehle in Phase 03.",
        "Delphi/Autocom nicht angebunden.",
        "Vgate nur vorbereitet, nicht hardwarefreigegeben.",
        "HTTPS-Browser: Localhost-HTTP (127.0.0.1) ist für Secure-Context-Ausnahmen üblich; Mixed-Content von HTTPS-Seiten zu http://127.0.0.1 ist je nach Browser eingeschränkt – Pairing lokal / Dev-Proxy nutzen, keine Sicherheitsabschaltung."
    }
}));

app.Run();

public partial class Program;

public sealed record PairRequest(string PairingCode);
public sealed record ConnectComRequest(string PortName, string? Transport = null, bool RunAtInit = false);
