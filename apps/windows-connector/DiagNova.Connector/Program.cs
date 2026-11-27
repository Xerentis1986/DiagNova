using System.Net;
using System.Runtime.InteropServices;
using DiagNova.Connector.Adapters;
using DiagNova.Connector.Adapters.DelphiCdp;
using DiagNova.Connector.Adapters.ObdDiag;
using DiagNova.Connector.Auth;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Ecu;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
using DiagNova.Connector.Protocol;
using DiagNova.Connector.Transport;
using DiagNova.Connector.Updates;

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
builder.Services.AddSingleton<AdapterRegistry>();
builder.Services.AddSingleton<HardwareInventoryProbe>();
builder.Services.AddSingleton<J2534PassThruAbstraction>();
builder.Services.AddSingleton<DelphiCdpAdapterService>();
builder.Services.AddSingleton<CdpFirmwareManager>();
builder.Services.AddSingleton<ObdDiagAdapterService>();
builder.Services.AddSingleton<LicenseGateService>();
builder.Services.AddSingleton<PairingService>();
builder.Services.AddSingleton<OriginGuard>();
builder.Services.AddSingleton<LocalAuthService>();
builder.Services.AddSingleton<ClearDtcGate>();
builder.Services.AddSingleton<UpdateBusyGate>();
builder.Services.AddSingleton<UpdateService>();

var app = builder.Build();
var log = app.Services.GetRequiredService<DiagnosticProtocolLog>();
var pairing = app.Services.GetRequiredService<PairingService>();

log.Info("startup", "DiagNova Connector Phase 14 startet", loopbackUrl);
log.Info("startup", "Pairing-Code erzeugt", pairing.GetPairingInfo().PairingCode);
Console.WriteLine($"DiagNova Connector {ConnectorVersion.Version} – Loopback {loopbackUrl}");
Console.WriteLine($"Pairing-Code: {pairing.GetPairingInfo().PairingCode} (gilt bis {pairing.GetPairingInfo().PairingExpiresAt:u})");
Console.WriteLine("Phase 14: Software-Updates Busy-Gate. Kein ungeprüftes Auto-Install. Kein Blindscan.");

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

app.MapGet("/health", (IDiagnosticAdapter adapter, AdapterRegistry registry) => Results.Json(new
{
    status = "ok",
    phase = 21,
    version = ConnectorVersion.Version,
    adapter = adapter.Name,
    selected_adapter_id = registry.SelectedAdapterId,
    data_source = adapter.DataSource,
    is_simulator = adapter.IsSimulator,
    platform = RuntimeInformation.OSDescription,
    message_de = "Connector Phase 21 – Multi-Adapter + Inventur. Keine erfundenen HW-Erfolge. Hardwarefreigabe ausstehend."
}));

app.MapGet("/version", () => Results.Json(new
{
    component = "connector",
    version = ConnectorVersion.Version,
    channel = ConnectorVersion.Channel,
    note_de = ConnectorVersion.PhaseNoteDe
}));

app.MapGet("/updates/status", (UpdateService updates) => Results.Json(updates.Status()));

app.MapGet("/updates/busy", (UpdateBusyGate gate) =>
{
    var snap = gate.Snapshot();
    return Results.Json(new
    {
        allowed = snap.Allowed,
        reason_de = snap.ReasonDe,
        blockers = snap.Blockers
    });
});

app.MapPost("/updates/busy/diagnosis/begin", (UpdateBusyGate gate) =>
{
    gate.BeginDiagnosis();
    return Results.Json(gate.Snapshot());
});

app.MapPost("/updates/busy/diagnosis/end", (UpdateBusyGate gate) =>
{
    gate.EndDiagnosis();
    return Results.Json(gate.Snapshot());
});

app.MapPost("/updates/stage", async (HttpRequest req, UpdateService updates) =>
{
    var body = await req.ReadFromJsonAsync<StageUpdateRequest>();
    if (body is null || string.IsNullOrWhiteSpace(body.TargetVersion))
    {
        return Results.BadRequest(new { error = "target_version_required" });
    }
    return Results.Json(updates.TryStageInstall(body.TargetVersion, body.AdminApproved));
});

app.MapPost("/updates/rollback", (UpdateService updates) => Results.Json(updates.Rollback()));

app.MapGet("/protocols", () => Results.Json(ProtocolCatalog.Summary()));
app.MapGet("/capability-matrix", () => Results.Json(AdapterCapabilityMatrix.Matrix()));
app.MapGet("/ecu/categories", () => Results.Json(MultiEcuService.CategoriesOverview()));

app.MapGet("/adapters", (AdapterRegistry registry) => Results.Json(registry.ListProfiles()));
app.MapGet("/adapters/{adapterId}", (string adapterId, AdapterRegistry registry) =>
{
    var profile = registry.GetProfile(adapterId);
    return profile is null ? Results.NotFound(new { error = "adapter_not_found" }) : Results.Json(profile);
});
app.MapPost("/adapters/select", async (HttpRequest req, AdapterRegistry registry) =>
{
    var body = await req.ReadFromJsonAsync<SelectAdapterRequest>();
    if (body is null || string.IsNullOrWhiteSpace(body.AdapterId))
    {
        return Results.BadRequest(new { error = "adapter_id_required" });
    }
    try
    {
        return Results.Json(registry.Select(body.AdapterId));
    }
    catch (InvalidOperationException ex)
    {
        return Results.NotFound(new { error = ex.Message });
    }
});
app.MapPost("/adapters/auto-detect", async (AdapterRegistry registry, CancellationToken ct) =>
    Results.Json(await registry.AutoDetectAsync(ct)));
app.MapPost("/adapters/connection-test", (AdapterRegistry registry) => Results.Json(registry.ConnectionTest()));
app.MapGet("/adapters/selected/capabilities", (AdapterRegistry registry) => Results.Json(registry.Capabilities()));
app.MapGet("/hardware/inventory", async (HardwareInventoryProbe probe, CancellationToken ct) =>
    Results.Json(await probe.ProbeAsync(ct)));
app.MapGet("/hardware/manufacturer-inquiry-draft", () => Results.Json(new
{
    draft_de = HardwareInventoryProbe.ManufacturerInquiryDraft(),
    note_de = "Nur Textvorlage – kein automatischer Versand an Hersteller."
}));
app.MapGet("/j2534/status", (J2534PassThruAbstraction j2534) => Results.Json(j2534.Describe()));
app.MapPost("/j2534/open", async (HttpRequest req, J2534PassThruAbstraction j2534) =>
{
    var body = await req.ReadFromJsonAsync<J2534OpenRequest>();
    return Results.Json(j2534.TryOpen(body?.DllPath));
});

app.MapGet("/adapters/delphi-cdp/status", (DelphiCdpAdapterService cdp) => Results.Json(cdp.Status()));
app.MapGet("/adapters/delphi-cdp/compatibility", (DelphiCdpAdapterService cdp) => Results.Json(cdp.Compatibility()));
app.MapGet("/adapters/delphi-cdp/encode-demo", (DelphiCdpAdapterService cdp) => Results.Json(cdp.EncodeDemo()));
app.MapPost("/adapters/delphi-cdp/identify-sim", async (DelphiCdpAdapterService cdp, CancellationToken ct) =>
    Results.Json(await cdp.IdentifySimulatedAsync(ct)));
app.MapPost("/adapters/delphi-cdp/open-live", (DelphiCdpAdapterService cdp) => Results.Json(cdp.TryOpenLive()));
app.MapPost("/adapters/delphi-cdp/vehicle-command", () => Results.Json(new
{
    ok = false,
    status = 403,
    message_de =
        "Fahrzeug-/CAN-/Relais-Befehle sind deaktiviert. " +
        "Keine ungeprüfte OBD-Pin-Umschaltung, kein ECU-Schreiben, kein Auto-Firmwareupdate."
}, statusCode: StatusCodes.Status403Forbidden));
app.MapGet("/adapters/delphi-cdp/firmware", (CdpFirmwareManager fw) => Results.Json(fw.Status()));
app.MapPost("/adapters/delphi-cdp/firmware/import", async (HttpRequest req, CdpFirmwareManager fw) =>
{
    // Multipart optional – JSON { label, content_base64, user_confirmed_rights }
    using var doc = await System.Text.Json.JsonDocument.ParseAsync(req.Body);
    var root = doc.RootElement;
    var label = root.TryGetProperty("label", out var l) ? l.GetString() ?? "package" : "package";
    var confirmed = root.TryGetProperty("user_confirmed_rights", out var c) && c.GetBoolean();
    var b64 = root.TryGetProperty("content_base64", out var b) ? b.GetString() : null;
    byte[] bytes;
    try { bytes = string.IsNullOrWhiteSpace(b64) ? Array.Empty<byte>() : Convert.FromBase64String(b64); }
    catch { return Results.Json(new { ok = false, message_de = "Ungültiges Base64" }, statusCode: 400); }
    return Results.Json(fw.ImportPackage(label, bytes, confirmed, root.TryGetProperty("notes", out var n) ? n.GetString() : null));
});
app.MapPost("/adapters/delphi-cdp/firmware/flash", async (HttpRequest req, CdpFirmwareManager fw) =>
{
    using var doc = await System.Text.Json.JsonDocument.ParseAsync(req.Body);
    var id = doc.RootElement.TryGetProperty("package_id", out var p) ? p.GetString() ?? "" : "";
    var confirm = doc.RootElement.TryGetProperty("user_confirm_flash", out var c) && c.GetBoolean();
    var result = fw.RequestFlash(id, confirm);
    return Results.Json(result, statusCode: StatusCodes.Status403Forbidden);
});

app.MapGet("/adapters/obd-diag/status", (ObdDiagAdapterService obd) => Results.Json(obd.Status()));
app.MapGet("/adapters/obd-diag/probe-guidance", (ObdDiagAdapterService obd) => Results.Json(obd.ProbeGuidance()));
app.MapPost("/adapters/obd-diag/inventory-probe", async (ObdDiagAdapterService obd, CancellationToken ct) =>
    Results.Json(await obd.InventoryProbeAsync(ct)));

app.MapGet("/license/gate", (LicenseGateService gate) => Results.Json(gate.Status()));
app.MapPost("/license/gate/apply", async (HttpRequest req, LicenseGateService gate) =>
{
    using var doc = await System.Text.Json.JsonDocument.ParseAsync(req.Body);
    var root = doc.RootElement;
    var allowed = root.TryGetProperty("allowed", out var a) && a.GetBoolean();
    var plan = root.TryGetProperty("plan_code", out var p) ? p.GetString() ?? "none" : "none";
    var hours = root.TryGetProperty("offline_hours", out var h) ? h.GetInt32() : 72;
    var msg = root.TryGetProperty("message_de", out var m) ? m.GetString() : null;
    return Results.Json(gate.ApplyServerVerification(allowed, plan, hours, msg));
});

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
app.MapPost("/obd/init", async (AdapterConnectionManager manager, LicenseGateService gate, CancellationToken ct) =>
{
    var statusJson = System.Text.Json.JsonSerializer.Serialize(manager.GetExtendedStatus());
    var simPath = statusJson.Contains("simulated", StringComparison.OrdinalIgnoreCase)
                  || statusJson.Contains("simulator", StringComparison.OrdinalIgnoreCase)
                  || statusJson.Contains("fake", StringComparison.OrdinalIgnoreCase);
    if (!gate.IsAllowed() && !simPath)
    {
        return Results.Json(new { error = "license_required", license = gate.Status() },
            statusCode: StatusCodes.Status402PaymentRequired);
    }
    try
    {
        return Results.Json(await manager.InitObdAsync(ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "obd_init_failed", message_de = ex.Message }, statusCode: 400);
    }
});

app.MapGet("/obd/live", async (AdapterConnectionManager manager, LicenseGateService gate, CancellationToken ct) =>
{
    var json = System.Text.Json.JsonSerializer.Serialize(manager.GetExtendedStatus());
    var sim = json.Contains("simulated", StringComparison.OrdinalIgnoreCase)
              || json.Contains("simulator", StringComparison.OrdinalIgnoreCase)
              || json.Contains("fake", StringComparison.OrdinalIgnoreCase);
    if (!gate.IsAllowed() && !sim)
        return Results.Json(new { error = "license_required", license = gate.Status() }, statusCode: StatusCodes.Status402PaymentRequired);
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

app.MapGet("/ecu/list", async (AdapterConnectionManager manager, bool? refresh, CancellationToken ct) =>
{
    try
    {
        return Results.Json(await manager.ListEcusAsync(refresh ?? true, ct));
    }
    catch (Exception ex)
    {
        return Results.Json(new { error = "ecu_list_failed", message_de = ex.Message }, statusCode: 400);
    }
});

// Bewusst kein Blindscan-Endpoint
app.MapPost("/ecu/blind-scan", () => Results.Json(new
{
    error = "blind_scan_forbidden",
    message_de = "Blindes Netzwerkscan ist deaktiviert. Nur beobachtete ISO-15765-4-OBD-Adressen."
}, statusCode: 403));

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
    phase = 5,
    vehicle_commands = true,
    vehicle_commands_allowlist_only = true,
    clear_dtc_requires_approval = true,
    blind_scan_allowed = false,
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
        multi_ecu_inventory = true,
        protocol_catalog = true,
        capability_matrix = true,
        uds_nrc_parser = true,
        isotp_documented = true,
        doip_prep_docs = true,
        j2534_prep_docs = true,
        j1939_planned_later = true,
        fake_port_tests = true,
        simulator_separate = true,
        browser_pairing = true,
        loopback_only = true,
        origin_guard = true,
        live_vs_demo_label = true,
        oem_abs_airbag_comfort = false
    },
    adapters = new object[]
    {
        new { id = "simulator", status = "available", note_de = "Separater Simulator-Pfad (data_source=simulated)" },
        new { id = "elm327-obd", status = "implemented_simulated", note_de = "OBD über Fake/Simulator getestet; kein DoIP/CAN-FD; Hardwarefreigabe ausstehend" },
        new { id = "j2534-passthru", status = "documented_prep", note_de = "Nur Dokumentation/Vorbereitung" },
        new { id = "doip-ethernet", status = "documented_prep", note_de = "Nur Dokumentation/Vorbereitung" },
        new { id = "vgate-vlinker-mc-plus", status = "blocked", note_de = "Windows-SPP-Variante nicht verifiziert (BLK-ADAPTER)" },
        new { id = "obd-diag-2055", status = "blocked", note_de = "Keine freie Entwickler-API nachgewiesen; ELM nicht angenommen" },
        new { id = "delphi-autocom", status = "partial_cdp_ascii_sim", note_de = "Eigenes CDP+-Safe-Read-Modul (*200/*201/*203/*20A); Live-FTDI/CAN gesperrt; hardware_tested=false" },
        new { id = "j2534-passthru", status = "planned", note_de = "Abstraktion ohne DLL-Bindung" }
    },
    limitations_de = new[]
    {
        "Kein realer Fahrzeugtest in dieser Umgebung – Parser/Simulator nur.",
        "Live-Hardwarepfad implementiert aber nicht hardwaregetestet / nicht freigegeben.",
        "Kein Blindscan unbekannter Netze.",
        "ABS/Airbag/Komfort ohne verifizierte OEM-Definitionen.",
        "DoIP/CAN-FD/J2534 nur vorbereitet, nicht implementiert.",
        "J1939/RP1210 → Phase 19.",
        "Delphi/Autocom CDP+: nur Geräte-Lese-Sim; kein Live-Labor, kein CAN/Relais/Flash.",
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
public sealed record StageUpdateRequest(string TargetVersion, bool AdminApproved = false);
public sealed record SelectAdapterRequest(string AdapterId);
public sealed record J2534OpenRequest(string? DllPath = null);
