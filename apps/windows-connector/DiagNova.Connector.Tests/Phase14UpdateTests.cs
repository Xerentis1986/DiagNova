using DiagNova.Connector.Updates;

namespace DiagNova.Connector.Tests;

public class Phase14UpdateTests
{
    [Fact]
    public void BusyGate_Blocks_During_Diagnosis()
    {
        var gate = new UpdateBusyGate();
        var svc = new UpdateService(gate);

        gate.BeginDiagnosis();
        var snap = gate.Snapshot();
        Assert.False(snap.Allowed);

        var result = svc.TryStageInstall("0.14.1", adminApproved: true);
        var status = result.GetType().GetProperty("status")!.GetValue(result) as string;
        Assert.Equal("blocked_busy", status);

        gate.EndDiagnosis();
        Assert.True(gate.Snapshot().Allowed);
    }

    [Fact]
    public void Install_Requires_Admin_Approval()
    {
        var svc = new UpdateService(new UpdateBusyGate());
        var pending = svc.TryStageInstall("0.14.1", adminApproved: false);
        Assert.Equal("awaiting_approval", pending.GetType().GetProperty("status")!.GetValue(pending) as string);

        var ok = svc.TryStageInstall("0.14.1", adminApproved: true);
        Assert.Equal("succeeded", ok.GetType().GetProperty("status")!.GetValue(ok) as string);
    }

    [Fact]
    public void Tampered_Checksum_Is_Rejected()
    {
        var svc = new UpdateService(new UpdateBusyGate());
        const string payload = "{\"component\":\"connector\",\"version\":\"0.14.1\"}";
        var verify = svc.VerifyPackage(payload, "deadbeef", "00", "secret");
        Assert.False((bool)verify.GetType().GetProperty("ok")!.GetValue(verify)!);
    }
}
