using DiagNova.Connector.Adapters;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
using DiagNova.Connector.Transport;
using Xunit;

namespace DiagNova.Connector.Tests;

public class ObdSessionTests
{
    [Fact]
    public void Parser_handles_multi_ecu_and_no_data()
    {
        var multi = ObdResponseParser.Parse("7E8 41 00 BE 1F A8 13\r\n7E9 41 00 88 18 80 00\r\n>");
        Assert.Equal(ObdResponseKind.Ok, multi.Kind);
        Assert.True(multi.MultiEcu);
        Assert.Equal(2, multi.Frames.Count);

        var noData = ObdResponseParser.Parse("NO DATA\r\n>");
        Assert.Equal(ObdResponseKind.NoData, noData.Kind);

        var timeout = ObdResponseParser.Parse(null, timedOut: true);
        Assert.Equal(ObdResponseKind.Timeout, timeout.Kind);

        var neg = ObdResponseParser.Parse("7E8 7F 01 11\r\n>");
        Assert.Equal(ObdResponseKind.Negative, neg.Kind);
    }

    [Fact]
    public void Pid_bitmap_and_dtc_decode()
    {
        // BE 1F A8 13 – classic vector supporting 01..20 subset
        var pids = ObdResponseParser.ParsePidBitmap(0x00, new byte[] { 0xBE, 0x1F, 0xA8, 0x13 });
        Assert.Contains(0x01, pids);
        Assert.Contains(0x0C, pids);
        Assert.Contains(0x0D, pids);
        Assert.Contains(0x20, pids);

        Assert.Equal("P0301", ObdResponseParser.DecodeDtc(0x03, 0x01));
        var dtcs = ObdResponseParser.ParseDtcPayload(0x4A, new byte[] { 0x01, 0x04, 0x20 }, "7E8");
        Assert.Single(dtcs);
        Assert.Equal("permanent", dtcs[0].Status);
        Assert.False(dtcs[0].Clearable);
    }

    [Fact]
    public void Rpm_scaler()
    {
        var reading = ObdPidScaler.Scale(0x0C, new byte[] { 0x1F, 0x40 }, "7E8");
        Assert.Equal("ok", reading.Status);
        Assert.Equal(2000.0, reading.Value);
    }

    [Fact]
    public async Task Session_init_live_dtc_ff_rdy_vin_on_fake()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var log = new DiagnosticProtocolLog();
        var session = new ObdSession(port, log, isSimulator: true, dataSource: "simulated");

        var init = await session.InitializeAsync();
        Assert.True(session.VehicleLinked);
        Assert.NotEmpty(session.SupportedPids);
        Assert.Contains("simulated", init.ToString()!);

        var live = await session.ReadLiveAsync();
        Assert.Contains("readings", live.ToString()!);

        var dtcs = await session.ReadDtcsAsync();
        var dtcText = System.Text.Json.JsonSerializer.Serialize(dtcs);
        Assert.Contains("P0301", dtcText);
        Assert.Contains("permanent", dtcText);
        Assert.Contains("Clearable\":false", dtcText, StringComparison.OrdinalIgnoreCase);

        var ff = await session.ReadFreezeFrameAsync();
        Assert.Contains("P0301", System.Text.Json.JsonSerializer.Serialize(ff));

        var rdy = await session.ReadReadinessAsync();
        Assert.Contains("mil_on", System.Text.Json.JsonSerializer.Serialize(rdy));

        var vin = await session.ReadVinAsync();
        var vinJson = System.Text.Json.JsonSerializer.Serialize(vin);
        Assert.Contains(ObdSimulatorResponses.DemoVin, vinJson);
        Assert.Contains("simulated", vinJson);
    }

    [Fact]
    public async Task Clear_requires_gate_and_consumes_token()
    {
        var gate = new ClearDtcGate(new DiagnosticProtocolLog());
        var denied = gate.IssueApproval("wrong", true, true, true, true, null);
        Assert.False(denied.Success);

        var warnings = gate.GetWarnings();
        Assert.NotNull(warnings);

        var ok = gate.IssueApproval(
            ClearApproval.RequiredPhrase,
            true, true, true, true, "test-op");
        Assert.True(ok.Success);
        Assert.NotNull(ok.Approval);

        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var session = new ObdSession(port, new DiagnosticProtocolLog(), true, "simulated");
        await session.InitializeAsync();

        Assert.True(gate.TryConsume(ok.Approval!.Token, out var approval, out _));
        var clear = await session.ClearDtcsAsync(approval!);
        Assert.Contains("success", System.Text.Json.JsonSerializer.Serialize(clear));

        // Token bereits verbraucht
        Assert.False(gate.TryConsume(ok.Approval.Token, out _, out _));
    }

    [Fact]
    public async Task Allowlist_rejects_unknown_command()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var session = new ObdSession(port, new DiagnosticProtocolLog(), true, "simulated");
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            session.TransactAllowedAsync("221234", CancellationToken.None));
    }

    [Fact]
    public async Task Disconnect_and_abort_paths()
    {
        var manager = new AdapterConnectionManager(
            new SerialTransportFactory(),
            new Elm327DriverPrep(new DiagnosticProtocolLog()),
            new DiagnosticProtocolLog());

        await manager.ConnectFakeAsync();
        Assert.True(manager.GetStatus().AdapterConnected);
        Assert.False(manager.GetStatus().VehicleConnected);

        await manager.InitObdAsync();
        Assert.True(manager.GetStatus().VehicleConnected);
        Assert.Equal("simulated", manager.DataSource);

        await manager.DisconnectAsync();
        Assert.False(manager.GetStatus().AdapterConnected);
        Assert.False(manager.GetStatus().VehicleConnected);
    }

    [Fact]
    public void Parser_empty_is_not_null_invented()
    {
        var empty = ObdResponseParser.Parse("   ");
        Assert.Equal(ObdResponseKind.Empty, empty.Kind);
        Assert.Contains("unbekannt", empty.MessageDe, StringComparison.OrdinalIgnoreCase);
    }
}
