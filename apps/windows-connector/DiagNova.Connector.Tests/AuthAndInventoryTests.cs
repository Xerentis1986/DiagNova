using DiagNova.Connector.Auth;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Adapters;
using DiagNova.Connector.Transport;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace DiagNova.Connector.Tests;

public class AuthAndInventoryTests
{
    private static IConfiguration EmptyConfig() =>
        new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>()).Build();

    [Fact]
    public void Pairing_issues_session_and_rotates_code()
    {
        var pairing = new PairingService(EmptyConfig());
        var info = pairing.GetPairingInfo();
        Assert.Equal(6, info.PairingCode.Length);

        Assert.True(pairing.TryPair(info.PairingCode, out var session));
        Assert.NotNull(session);
        Assert.True(pairing.IsSessionValid(session!.Token));

        // Code rotiert – alter Code ungültig
        Assert.False(pairing.TryPair(info.PairingCode, out _));
    }

    [Fact]
    public void Bootstrap_connector_token_is_accepted()
    {
        var config = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["CONNECTOR_TOKEN"] = "test-bootstrap-token"
        }).Build();
        var pairing = new PairingService(config);
        Assert.True(pairing.IsSessionValid("test-bootstrap-token"));
    }

    [Fact]
    public void Origin_guard_allows_loopback_and_rejects_foreign()
    {
        var guard = new OriginGuard(EmptyConfig());
        var ctx = new DefaultHttpContext();
        ctx.Request.Headers.Origin = "http://127.0.0.1:5173";
        Assert.True(guard.IsOriginAllowed(ctx.Request));

        ctx.Request.Headers.Origin = "https://evil.example";
        Assert.False(guard.IsOriginAllowed(ctx.Request));

        // Ohne Origin (curl): erlaubt
        var ctx2 = new DefaultHttpContext();
        Assert.True(guard.IsOriginAllowed(ctx2.Request));
    }

    [Fact]
    public void Local_auth_requires_bearer_for_protected_paths()
    {
        var pairing = new PairingService(new ConfigurationBuilder().AddInMemoryCollection(
            new Dictionary<string, string?> { ["CONNECTOR_TOKEN"] = "secret" }).Build());
        var guard = new OriginGuard(EmptyConfig());
        var auth = new LocalAuthService(pairing, guard);

        var publicReq = new DefaultHttpContext().Request;
        publicReq.Path = "/pair/info";
        Assert.True(auth.IsAuthorized(publicReq));

        var protectedReq = new DefaultHttpContext().Request;
        protectedReq.Path = "/devices";
        Assert.False(auth.IsAuthorized(protectedReq));

        protectedReq.Headers.Authorization = "Bearer secret";
        Assert.True(auth.IsAuthorized(protectedReq));
    }

    [Fact]
    public async Task Inventory_includes_simulator_and_limitations()
    {
        var bt = new BluetoothScanner(new[]
        {
            new DiscoveredDevice("bt:AA:BB:CC:DD:EE:FF", DeviceKind.BluetoothSpp, "Fake OBD",
                null, "AA:BB:CC:DD:EE:FF", "possible-obd-adapter", true, true, "test", "injiziert")
        });
        var usb = new UsbScanner(Array.Empty<DiscoveredDevice>());
        var inventory = new CompositeDeviceInventory(new ComPortScanner(), bt, usb);
        var snap = await inventory.ScanAsync();
        Assert.Contains(snap.Devices, d => d.Kind == DeviceKind.Simulator);
        Assert.Contains(snap.Devices, d => d.Id == "bt:AA:BB:CC:DD:EE:FF");
        Assert.Contains(snap.LimitationsDe, l => l.Contains("Delphi/Autocom", StringComparison.OrdinalIgnoreCase));
        Assert.Contains(snap.LimitationsDe, l => l.Contains("Vgate", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task Connection_manager_separates_adapter_and_vehicle()
    {
        var manager = new AdapterConnectionManager(
            new SerialTransportFactory(),
            new Elm327DriverPrep(new DiagnosticProtocolLog()),
            new DiagnosticProtocolLog());

        var status = manager.GetStatus();
        Assert.False(status.VehicleConnected);

        await manager.ConnectFakeAsync();
        status = manager.GetStatus();
        Assert.True(status.AdapterConnected);
        Assert.False(status.VehicleConnected); // vor OBD-Init
        Assert.Equal("adapter_fake", manager.DataSource);

        await manager.InitObdAsync();
        Assert.True(manager.GetStatus().VehicleConnected);

        await manager.SelectSimulatorAsync();
        Assert.True(manager.IsSimulator);
        Assert.False(manager.GetStatus().VehicleConnected); // Simulator neu, noch ohne Init

        await manager.DisconnectAsync();
        Assert.False(manager.GetStatus().AdapterConnected);
    }

    [Fact]
    public void Protocol_log_keeps_ring_buffer()
    {
        var log = new DiagnosticProtocolLog(capacity: 50);
        for (var i = 0; i < 80; i++)
        {
            log.Info("test", $"msg-{i}");
        }
        var snap = log.Snapshot(100);
        Assert.True(snap.Count <= 50);
        Assert.Contains(snap, e => e.Message == "msg-79");
    }
}
