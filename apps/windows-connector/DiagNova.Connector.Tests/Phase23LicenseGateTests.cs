using DiagNova.Connector.Auth;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase23LicenseGateTests
{
    [Fact]
    public void Signed_token_valid_allows()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_test_device_001");
        var gate = new LicenseGateService();
        Assert.Equal("dev_test_device_001", gate.DeviceId);
        var payload = LicenseGateService.IssueTestToken(
            gate.DeviceId, "ws1", "pro", 12, allowed: true);
        var sig = LicenseGateService.ComputeHmacHex(payload);
        dynamic st = gate.ApplySignedToken(payload, sig);
        Assert.True((bool)st.GetType().GetProperty("allowed")!.GetValue(st)!);
    }

    [Fact]
    public void Tampered_signature_denied()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_test_device_002");
        var gate = new LicenseGateService();
        var payload = LicenseGateService.IssueTestToken(gate.DeviceId, "ws1", "pro", 12);
        var bad = gate.ApplySignedToken(payload, "00" + LicenseGateService.ComputeHmacHex(payload)[2..]);
        Assert.False((bool)bad.GetType().GetProperty("allowed")!.GetValue(bad)!);
    }

    [Fact]
    public void Foreign_device_denied()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_local_aaa");
        var gate = new LicenseGateService();
        var payload = LicenseGateService.IssueTestToken("dev_other_bbb", "ws1", "pro", 12);
        var sig = LicenseGateService.ComputeHmacHex(payload);
        var st = gate.ApplySignedToken(payload, sig);
        Assert.False((bool)st.GetType().GetProperty("allowed")!.GetValue(st)!);
    }

    [Fact]
    public void Expired_token_denied()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_exp_ccc");
        var gate = new LicenseGateService();
        var payload = LicenseGateService.IssueTestToken(gate.DeviceId, "ws1", "pro", validHours: -1);
        // IssueTestToken with -1 hours → past exp
        var sig = LicenseGateService.ComputeHmacHex(payload);
        var st = gate.ApplySignedToken(payload, sig);
        Assert.False((bool)st.GetType().GetProperty("allowed")!.GetValue(st)!);
    }

    [Fact]
    public void Revoke_blocks()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_rev_ddd");
        var gate = new LicenseGateService();
        gate.ApplyServerVerification(true, "pro", 24, "ok");
        Assert.True(gate.IsAllowed());
        gate.Revoke();
        Assert.False(gate.IsAllowed());
    }

    [Fact]
    public void Demo_path_allowed_without_paid()
    {
        var gate = new LicenseGateService();
        Assert.True(gate.AllowsDemoPath(true));
        Assert.False(gate.IsAllowed());
    }
}
