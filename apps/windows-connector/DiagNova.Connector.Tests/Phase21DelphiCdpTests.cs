using DiagNova.Connector.Adapters.DelphiCdp;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase21DelphiCdpTests
{
    [Fact]
    public void Encode_Uses_Star_And_Cr()
    {
        var framed = CdpProtocol.EncodeCommand("200");
        Assert.Equal("*200\r", framed);
        var withArgs = CdpProtocol.EncodeCommand("668", "0", "500", "7E0", "7E8");
        Assert.Equal("*668_0_500_7E0_7E8\r", withArgs);
    }

    [Fact]
    public void Parse_Documented_Serial_And_Battery()
    {
        var serial = CdpProtocol.ParseResponse("*1 100251\r");
        Assert.True(serial.Ok);
        Assert.Equal("100251", serial.Payload);
        Assert.True(CdpCompatibility.SerialLooksLikeDocumentedFamily(serial.Payload));

        Assert.True(CdpProtocol.TryParseBatteryVolts("*0 1362\r", out var v));
        Assert.Equal(13.62, v, 3);
    }

    [Fact]
    public void Vehicle_Commands_Are_Classified()
    {
        Assert.True(CdpProtocol.IsSafeDeviceRead("200"));
        Assert.True(CdpProtocol.IsVehicleOrRelayCommand("668"));
        Assert.True(CdpProtocol.IsVehicleOrRelayCommand("606B001"));
        Assert.True(CdpProtocol.IsVehicleOrRelayCommand("608"));
    }

    [Fact]
    public async Task Session_Reads_Identity_On_Fake_Transport()
    {
        var log = new DiagnosticProtocolLog();
        await using var transport = new FakeCdpTransport();
        await using var session = new CdpSession(transport, log, allowVehicleCommands: false);
        await session.OpenAsync();
        var id = await session.ReadIdentityAsync();
        Assert.Equal("100251", id.SerialPayload);
        Assert.Equal("1622", id.FirmwarePayload);
        Assert.True(id.SerialMatchesOperatorFamily);
        Assert.False(id.HardwareTested);
        Assert.Equal("simulated", id.DataSource);
        Assert.NotNull(id.BatteryVolts);
    }

    [Fact]
    public async Task Session_Blocks_Can_Config_Without_Release()
    {
        var log = new DiagnosticProtocolLog();
        await using var transport = new FakeCdpTransport();
        await using var session = new CdpSession(transport, log, allowVehicleCommands: false);
        await session.OpenAsync();
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            session.SendVehicleCommandAsync("668", ["0", "500", "7E0", "7E8"]));
    }

    [Fact]
    public void Ftdi_Live_Open_Fails_Honestly_Without_Hardware()
    {
        var inventory = new CompositeDeviceInventory(new ComPortScanner(), new BluetoothScanner(), new UsbScanner());
        var svc = new DelphiCdpAdapterService(new DiagnosticProtocolLog(), inventory);
        var result = svc.TryOpenLive();
        var ok = (bool)result.GetType().GetProperty("ok")!.GetValue(result)!;
        Assert.False(ok);
    }
}
