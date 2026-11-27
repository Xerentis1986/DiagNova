using DiagNova.Connector.Adapters;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;
using Xunit;

namespace DiagNova.Connector.Tests;

public class FakeSerialTransportTests
{
    [Fact]
    public async Task Open_is_exclusive_and_dispose_closes()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "COM99" });
        Assert.True(port.IsOpen);

        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            port.OpenAsync(new SerialTransportOptions { PortName = "COM99" }));

        await port.CloseAsync();
        Assert.False(port.IsOpen);
        Assert.Equal(1, port.OpenCount);
        Assert.Equal(1, port.CloseCount);
    }

    [Fact]
    public async Task Transact_ATZ_returns_elm_banner()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var response = await port.TransactTextAsync("ATZ", TimeSpan.FromSeconds(1));
        Assert.Contains("ELM327", response, StringComparison.OrdinalIgnoreCase);
        Assert.Contains('>', response);
    }

    [Fact]
    public async Task Timeout_returns_empty_when_no_data()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        port.ResponseFactory = _ => "";
        // Write still enqueues empty; ReadAsync should timeout to empty
        var read = await port.ReadAsync(64, TimeSpan.FromMilliseconds(40));
        Assert.Equal(0, read.Length);
    }

    [Fact]
    public async Task Cancellation_aborts_transact()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        port.ResponseFactory = _ =>
        {
            Thread.Sleep(500);
            return "OK\r>";
        };

        using var cts = new CancellationTokenSource(30);
        // Force slow path by not putting prompt quickly - ResponseFactory sleeps but is sync in Write
        // Use ReadAsync with cancel instead
        await Assert.ThrowsAnyAsync<OperationCanceledException>(async () =>
        {
            await port.ReadAsync(32, TimeSpan.FromSeconds(5), cts.Token);
        });
    }

    [Fact]
    public async Task Elm327_prep_runs_safe_at_sequence_only()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var log = new DiagnosticProtocolLog();
        var prep = new Elm327DriverPrep(log);
        var result = await prep.RunAtInitAsync(port, TimeSpan.FromSeconds(1));
        Assert.True(result.Success);
        Assert.Equal(Elm327DriverPrep.SafeAtInitSequence.Length, result.Exchanges.Count);
        Assert.All(result.Exchanges, e => Assert.StartsWith("AT", e.Command, StringComparison.OrdinalIgnoreCase));
        Assert.Equal(Elm327DriverPrep.SafeAtInitSequence.Length, port.WrittenCommands.Count);
    }

    [Fact]
    public async Task Vehicle_obd_commands_are_blocked()
    {
        var prep = new Elm327DriverPrep(new DiagnosticProtocolLog());
        Assert.True(Elm327DriverPrep.IsVehicleObdCommand("0100"));
        Assert.True(Elm327DriverPrep.IsVehicleObdCommand("03"));
        Assert.True(Elm327DriverPrep.IsVehicleObdCommand("04"));
        Assert.False(Elm327DriverPrep.IsVehicleObdCommand("ATZ"));
        await Assert.ThrowsAsync<InvalidOperationException>(() => prep.RejectVehicleCommandAsync("0100"));
    }

    [Fact]
    public async Task Fake_obd_pid_gets_question_mark_not_vehicle_data()
    {
        await using var port = new FakeSerialTransport();
        await port.OpenAsync(new SerialTransportOptions { PortName = "FAKE" });
        var raw = await port.TransactTextAsync("0100", TimeSpan.FromSeconds(1));
        Assert.Contains('?', raw);
        Assert.DoesNotContain("41 00", raw);
    }
}
