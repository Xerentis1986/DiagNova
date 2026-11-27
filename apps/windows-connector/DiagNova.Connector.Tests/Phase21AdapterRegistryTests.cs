using DiagNova.Connector.Adapters;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase21AdapterRegistryTests
{
    private static AdapterRegistry CreateRegistry()
    {
        var log = new DiagnosticProtocolLog();
        var manager = new AdapterConnectionManager(
            new SerialTransportFactory(),
            new Elm327DriverPrep(log),
            log);
        var inventory = new CompositeDeviceInventory(
            new ComPortScanner(),
            new BluetoothScanner(),
            new UsbScanner());
        return new AdapterRegistry(manager, inventory, log);
    }

    [Fact]
    public void Catalog_Contains_ObdDiag_And_Delphi_Blocked()
    {
        var obd = AdapterCatalog.Get("obd-diag-2055");
        Assert.NotNull(obd);
        Assert.Equal(AdapterCompatibilityStatus.BlockedUndocumented, obd!.Status);
        Assert.False(obd.HardwareTested);
        Assert.False(obd.LawfulToIntegrate);

        var delphi = AdapterCatalog.Get("delphi-autocom");
        Assert.NotNull(delphi);
        Assert.Equal(AdapterCompatibilityStatus.ManufacturerApprovalRequired, delphi!.Status);
        Assert.False(delphi.ManufacturerApiDocumented);
    }

    [Fact]
    public void Select_Blocked_Adapter_Does_Not_Switch()
    {
        var registry = CreateRegistry();
        var result = registry.Select("obd-diag-2055");
        var ok = (bool)result.GetType().GetProperty("ok")!.GetValue(result)!;
        Assert.False(ok);
        Assert.Equal("simulator", registry.SelectedAdapterId);
    }

    [Fact]
    public void Select_Simulator_Works()
    {
        var registry = CreateRegistry();
        var result = registry.Select("simulator");
        var ok = (bool)result.GetType().GetProperty("ok")!.GetValue(result)!;
        Assert.True(ok);
        Assert.Equal("simulator", registry.SelectedAdapterId);
    }

    [Fact]
    public void J2534_Does_Not_Open_Dll()
    {
        var j = new J2534PassThruAbstraction();
        var opened = j.TryOpen("C:\\fake\\PassThru.dll");
        Assert.False((bool)opened.GetType().GetProperty("ok")!.GetValue(opened)!);
        var desc = j.Describe();
        Assert.Equal(false, desc.GetType().GetProperty("dll_bound")!.GetValue(desc));
        Assert.Equal(false, desc.GetType().GetProperty("hardware_tested")!.GetValue(desc));
    }

    [Fact]
    public async Task Hardware_Inventory_Is_Read_Only()
    {
        var inventory = new CompositeDeviceInventory(
            new ComPortScanner(),
            new BluetoothScanner(),
            new UsbScanner());
        var probe = new HardwareInventoryProbe(inventory);
        var result = await probe.ProbeAsync();
        Assert.Equal(false, result.GetType().GetProperty("hardware_tested")!.GetValue(result));
        Assert.Equal(false, result.GetType().GetProperty("vehicle_commands_sent")!.GetValue(result));
    }
}
