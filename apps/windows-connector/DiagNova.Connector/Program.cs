using System.Net;
using System.Runtime.InteropServices;
using DiagNova.Connector.Adapters;
using DiagNova.Connector.Auth;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
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
builder.Services.AddSingleton<ClearDtcGate>();

var app = builder.Build();
var log = app.Services.GetRequiredService<DiagnosticProtocolLog>();
var pairing = app.Services.GetRequiredService<PairingService>();

log.Info("startup", "DiagNova Connector Phase 04 startet", loopbackUrl);
log.Info("startup", "Pairing-Code erzeugt", pairing.GetPairingInfo().PairingCode);
Console.WriteLine($"DiagNova Connector – Loopback {loopbackUrl}");
Console.WriteLine($"Pairing-Code: {pairing.GetPairingInfo().PairingCode} (gilt bis {pairing.GetPairingInfo().PairingExpiresAt:u})");
Console.WriteLine("Phase 04: OBD-II lesen + freigabegeschütztes Clear DTC. Live/Demo getrennt.");

app.Use(async (ctx, next) =>
{
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
    phase = 4,
    adapter = adapter.Name,
    data_source = adapter.DataSource,
    is_simulator = adapter.IsSimulator,
    platform = RuntimeInformation.OSDescription,
    message_de = "Connector Phase 04 – OBD-II/EOBD (Allowlist). Hardwarefreigabe ausstehend."
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

// —— Phase 04 OBD ——
app.MapPost("/obd/init", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.InitObdAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_init_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/live", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ReadLiveAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_live_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/dtcs", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ReadDtcsAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_dtc_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/freeze-frame", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ReadFreezeFrameAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_ff_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/readiness", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ReadReadinessAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_rdy_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/vin", async (AdapterConnectionManager manager, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ReadVinAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_vin_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/clear/warnings", (ClearDtcGate gate) => Results.Json(gate.GetWarnings()));

app.MapPost("/obd/clear/approve", async (HttpRequest req, ClearDtcGate gate) =>
{
    var body = await req.ReadFromJsonAsync<ClearApproveRequest>();
    if (body is null)
    {
        return Results.BadRequest(new { error = "body_required" });
    }
    var result = gate.IssueApproval(
        body.ConfirmationPhrase,
        body.AcknowledgeFreezeFrameLoss,
        body.AcknowledgeReadinessReset,
        body.AcknowledgePermanentRemain,
        body.PreReportSaved,
        body.OperatorNote);
    if (!result.Success || result.Approval is null)
    {
        return Results.Json(new { error = "approval_denied", message_de = result.MessageDe }, statusCode: 400);
    }
    return Results.Json(new
    {
        success = true,
        token = result.Approval.Token,
        expires_at = result.Approval.ExpiresAt,
        message_de = result.MessageDe
    });
});

app.MapPost("/obd/dtc/clear", async (HttpRequest req, ClearDtcGate gate, AdapterConnectionManager manager, CancellationToken ct) =>
{
    var body = await req.ReadFromJsonAsync<ClearDtcRequest>();
    if (body is null || string.IsNullOrWhiteSpace(body.ApprovalToken))
    {
        return Results.BadRequest(new { error = "approval_token_required", message_de = "Freigabe-Token erforderlich." });
    }
    if (!gate.TryConsume(body.ApprovalToken, out var approval, out var msg) || approval is null)
    {
        return Results.Json(new { error = "invalid_approval", message_de = msg }, statusCode: 403);
    }
    try
    {
        var result = await manager.ClearDtcsAsync(approval, ct);
        return Results.Json(result);
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "clear_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/capabilities", () => Results.Json(new
{
    phase = 4,
    vehicle_commands = true,
    vehicle_commands_allowlist_only = true,
    clear_dtc_requires_approval = true,
    features = new
    {
        device_discovery = true,
        bluetooth_paired_list = true,
        com_usb_inventory = true,
        connection_status_separated = true,
        diagnostic_protocol_log = true,
        elm327_at_prep = true,
        obd_init_protocol = true,
        obd_pid_bitmap = true,
        obd_live = true,
        obd_dtc_stored_pending_permanent = true,
        obd_freeze_frame = true,
        obd_readiness = true,
        obd_vin = true,
        obd_clear_gated = true,
        multi_ecu = true,
        fake_port_tests = true,
        simulator_separate = true,
        browser_pairing = true,
        loopback_only = true,
        origin_guard = true,
        live_vs_demo_label = true
    },
    adapters = new object[]
    {
        new { id = "simulator", status = "available", note_de = "Separater Simulator-Pfad (data_source=simulated)" },
        new { id = "elm327-obd", status = "implemented_simulated", note_de = "OBD über Fake/Simulator getestet; Hardwarefreigabe ausstehend" },
        new { id = "vgate-vlinker-mc-plus", status = "blocked", note_de = "Windows-SPP-Variante nicht verifiziert (BLK-ADAPTER)" },
        new { id = "delphi-autocom", status = "blocked", note_de = "Keine dokumentierte öffentliche Schnittstelle" }
    },
    limitations_de = new[]
    {
        "Kein realer Fahrzeugtest in dieser Umgebung – Parser/Simulator nur.",
        "Live-Hardwarepfad implementiert aber nicht hardwaregetestet / nicht freigegeben.",
        "Delphi/Autocom nicht angebunden.",
        "Mode 04 nur mit Freigabe; permanente DTCs nicht löschbar.",
        "HTTPS-Browser: Mixed-Content zu http://127.0.0.1 je nach Browser eingeschränkt."
    }
}));

app.Run();

public partial class Program;

public sealed record PairRequest(string PairingCode);
public sealed record ConnectComRequest(string PortName, string? Transport = null, bool RunAtInit = true);
public sealed record ClearApproveRequest(
    string ConfirmationPhrase,
    bool AcknowledgeFreezeFrameLoss,
    bool AcknowledgeReadinessReset,
    bool AcknowledgePermanentRemain,
    bool PreReportSaved,
    string? OperatorNote = null);
public sealed record ClearDtcRequest(string ApprovalToken);
