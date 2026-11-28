using DiagNova.Connector.Adapters.DelphiCdp;
using DiagNova.Connector.Adapters.ObdDiag;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase21FirmwareAndObdDiagTests
{
    [Fact]
    public void Firmware_Import_Requires_Rights_And_Flash_Blocked()
    {
        var dir = Path.Combine(Path.GetTempPath(), "diagnova-fw-" + Guid.NewGuid().ToString("N"));
        var fw = new CdpFirmwareManager(dir);
        var denied = fw.ImportPackage("x", new byte[] { 1, 2, 3 }, userConfirmedLawfulRights: false);
        Assert.False((bool)denied.GetType().GetProperty("ok")!.GetValue(denied)!);

        var ok = fw.ImportPackage("lab", new byte[] { 1, 2, 3, 4 }, userConfirmedLawfulRights: true);
        Assert.True((bool)ok.GetType().GetProperty("ok")!.GetValue(ok)!);

        var flash = fw.RequestFlash("any", userConfirmFlash: true);
        Assert.False((bool)flash.GetType().GetProperty("ok")!.GetValue(flash)!);
    }

    [Fact]
    public void ObdDiag_Remains_Blocked_Without_Invented_Success()
    {
        var inventory = new DiagNova.Connector.Discovery.CompositeDeviceInventory(
            new DiagNova.Connector.Discovery.ComPortScanner(),
            new DiagNova.Connector.Discovery.BluetoothScanner(),
            new DiagNova.Connector.Discovery.UsbScanner());
        var svc = new ObdDiagAdapterService(inventory);
        var status = svc.Status();
        Assert.Equal(false, status.GetType().GetProperty("elm327_assumed")!.GetValue(status));
        Assert.Equal(false, status.GetType().GetProperty("hardware_tested")!.GetValue(status));
        Assert.Equal(
            "BlockedUndocumented",
            status.GetType().GetProperty("compatibility")!.GetValue(status));
    }
}
