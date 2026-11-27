using DiagNova.Connector.Adapters;
using DiagNova.Connector.Ecu;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
using DiagNova.Connector.Protocol;
using DiagNova.Connector.Transport;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase05MultiProtocolTests
{
    [Fact]
    public void Protocol_catalog_and_capability_matrix_exist()
    {
        var catalog = ProtocolCatalog.Summary();
        Assert.Contains("protocols", catalog.ToString()!);
        var matrix = AdapterCapabilityMatrix.Matrix();
        var json = System.Text.Json.JsonSerializer.Serialize(matrix);
        Assert.Contains("elm327-obd", json);
        Assert.Contains("not_supported", json);
        Assert.Contains("iso_13400_doip", json);
    }

    [Fact]
    public void Obd_addresses_reject_non_standard()
    {
        Assert.True(ObdEcuAddresses.IsStandardResponse("7E8"));
        Assert.True(ObdEcuAddresses.IsStandardResponse("7E9"));
        Assert.False(ObdEcuAddresses.IsStandardResponse("713"));
        Assert.Equal("7E8", ObdEcuAddresses.Normalize("07e8"));
    }

    [Fact]
    public void Uds_nrc_parser()
    {
        Assert.Equal("serviceNotSupported", UdsNrc.Decode(0x11));
        var parsed = UdsNrc.Parse(new byte[] { 0x7F, 0x22, 0x31 });
        Assert.NotNull(parsed);
        Assert.Equal(0x22, parsed!.Value.RequestSid);
        Assert.Equal("requestOutOfRange", parsed.Value.Name);
        Assert.Null(UdsNrc.Parse(new byte[] { 0x62, 0xF1, 0x90 }));
    }

    [Fact]
    public async Task Multi_ecu_inventory_from_simulator_no_blind_scan()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var session = new ObdSession(port, new DiagnosticProtocolLog(), true, "simulated");
        await session.InitializeAsync();

        var list = await session.ListEcusAsync();
        var json = System.Text.Json.JsonSerializer.Serialize(list);
        Assert.Contains("7E8", json);
        Assert.Contains("7E9", json);
        Assert.Contains("\"blind_scan_used\":false", json);
        Assert.Contains("abs", json);
        Assert.Contains("simulated", json);
    }

    [Fact]
    public async Task Manager_list_ecus_after_init()
    {
        var manager = new AdapterConnectionManager(
            new SerialTransportFactory(),
            new Elm327DriverPrep(new DiagnosticProtocolLog()),
            new DiagnosticProtocolLog());
        await manager.ConnectFakeAsync();
        await manager.InitObdAsync();
        var result = await manager.ListEcusAsync();
        var json = System.Text.Json.JsonSerializer.Serialize(result);
        Assert.Contains("discovered_obd_ecus", json);
        Assert.DoesNotContain("blind_scan_used\":true", json);
    }

    [Fact]
    public void Categories_mark_oem_unavailable()
    {
        var cats = System.Text.Json.JsonSerializer.Serialize(MultiEcuService.CategoriesOverview());
        Assert.Contains("unavailable_no_definition", cats);
        Assert.Contains("BLK-OEM", cats);
    }
}
