using DiagNova.Connector.Adapters;
using DiagNova.Connector.Adapters.Vgate;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase25VgateAdapterTests
{
    private static VgateIcarPro2sAdapterService CreateSvc()
    {
        var log = new DiagnosticProtocolLog();
        return new VgateIcarPro2sAdapterService(
            new CompositeDeviceInventory(new ComPortScanner(), new BluetoothScanner(), new UsbScanner()),
            new SerialTransportFactory(),
            new Elm327DriverPrep(log),
            log);
    }

    [Fact]
    public void Catalog_contains_vgate_icar_pro_2s()
    {
        var p = AdapterCatalog.Get("vgate-icar-pro-2s");
        Assert.NotNull(p);
        Assert.Contains("Vgate iCar Pro 2S", p!.DisplayNameDe);
        Assert.Equal(AdapterCompatibilityStatus.DriverPresent, p.Status);
        Assert.False(p.HardwareTested);
        Assert.Contains("bluetooth-rfcomm", p.Transports);
    }

    [Fact]
    public async Task Connection_test_without_port_is_honest_fail()
    {
        var r = await CreateSvc().ConnectionTestAsync(null);
        Assert.False((bool)r.GetType().GetProperty("ok")!.GetValue(r)!);
    }

    [Fact]
    public async Task Connection_test_fake_port_ok()
    {
        var r = await CreateSvc().ConnectionTestAsync("COM99");
        Assert.True((bool)r.GetType().GetProperty("ok")!.GetValue(r)!);
    }

    [Fact]
    public void Select_vgate_ok()
    {
        var log = new DiagnosticProtocolLog();
        var reg = new AdapterRegistry(
            new AdapterConnectionManager(new SerialTransportFactory(), new Elm327DriverPrep(log), log),
            new CompositeDeviceInventory(new ComPortScanner(), new BluetoothScanner(), new UsbScanner()),
            log);
        var sel = reg.Select("vgate-icar-pro-2s");
        Assert.True((bool)sel.GetType().GetProperty("ok")!.GetValue(sel)!);
        Assert.Equal("vgate-icar-pro-2s", reg.SelectedAdapterId);
    }
}
