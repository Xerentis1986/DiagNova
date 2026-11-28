using System.Security.Cryptography;
using System.Text;
using DiagNova.Connector.Auth;
using Xunit;

namespace DiagNova.Connector.Tests;

public class Phase24AsymmetricLicenseTests
{
    private static string? FindPrivatePem()
    {
        var candidates = new[]
        {
            Path.Combine(AppContext.BaseDirectory, "license_rsa_private.demo.pem"),
            Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "license_rsa_private.demo.pem"),
            Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "tests", "fixtures", "license_rsa_private.demo.pem")),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "license_rsa_private.demo.pem")),
        };
        return candidates.Select(Path.GetFullPath).FirstOrDefault(File.Exists);
    }

    private static string SignRsa(string payload, string privatePem)
    {
        using var rsa = RSA.Create();
        rsa.ImportFromPem(privatePem);
        var sig = rsa.SignData(Encoding.UTF8.GetBytes(payload), HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        return Convert.ToBase64String(sig);
    }

    [Fact]
    public void Rsa_token_valid_allows()
    {
        var pemPath = FindPrivatePem();
        Assert.True(pemPath is not null, "Demo private PEM fixture fehlt");
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_rsa_ok_001");
        var gate = new LicenseGateService();
        var payload = LicenseGateService.IssueTestToken(gate.DeviceId, "ws1", "pro", 12, alg: "RSA-SHA256");
        var sig = SignRsa(payload, File.ReadAllText(pemPath!));
        dynamic st = gate.ApplySignedToken(payload, sig, "RSA-SHA256-PKCS1v15");
        Assert.True((bool)st.GetType().GetProperty("allowed")!.GetValue(st)!);
    }

    [Fact]
    public void Rsa_forged_signature_denied()
    {
        Environment.SetEnvironmentVariable("DIAGNOVA_DEVICE_ID", "dev_rsa_bad_002");
        var gate = new LicenseGateService();
        var payload = LicenseGateService.IssueTestToken(gate.DeviceId, "ws1", "pro", 12, alg: "RSA-SHA256");
        var forged = Convert.ToBase64String(Encoding.UTF8.GetBytes(new string('A', 256)));
        var st = gate.ApplySignedToken(payload, forged, "RSA-SHA256-PKCS1v15");
        Assert.False((bool)st.GetType().GetProperty("allowed")!.GetValue(st)!);
    }

    [Fact]
    public void Public_key_loads()
    {
        var pem = LicenseGateService.LoadPublicKeyPem();
        Assert.Contains("BEGIN PUBLIC KEY", pem);
    }
}
