using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// Sichere Firmwareverwaltung: Erkennung, Kompatibilitätsmatrix, Import mit Integrität.
/// Kein automatisches Flashen. Keine proprietären Firmware-Binaries im Repo.
/// </summary>
public sealed class CdpFirmwareManager
{
    private readonly string _storeDir;

    public CdpFirmwareManager(string? storeDir = null)
    {
        _storeDir = storeDir
            ?? Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "DiagNova",
                "firmware-store");
        Directory.CreateDirectory(_storeDir);
    }

    public object Status(string? detectedFirmwarePayload = null) => new
    {
        auto_flash = false,
        flash_implemented = false,
        detected_firmware = detectedFirmwarePayload,
        operator_host_software = new[] { "2017.R3", "2020.23" },
        note_de =
            "Beim Wechsel 2017.R3 ↔ 2020.23 ist laut Betreiber ein Firmwareupdate nötig. " +
            "DiagNova führt kein automatisches Update durch. Ob ein gemeinsamer FW-Stand beide " +
            "Host-Varianten abdeckt, ist laboroffen.",
        store_dir = _storeDir,
        imported_packages = ListImported().Select(p => new
        {
            p.Id,
            p.Label,
            p.Sha256,
            p.Bytes,
            p.ImportedAtUtc,
            p.UserConfirmedRights
        }).ToArray(),
        compatibility = CdpCompatibility.Matrix()
    };

    public object ImportPackage(
        string label,
        byte[] content,
        bool userConfirmedLawfulRights,
        string? notes = null)
    {
        if (!userConfirmedLawfulRights)
        {
            return new
            {
                ok = false,
                message_de =
                    "Import verweigert: Nutzerbestätigung der rechtmäßigen Nutzung fehlt. " +
                    "Keine proprietären Firmwaredateien ohne Rechte."
            };
        }

        if (content.Length == 0 || content.Length > 32 * 1024 * 1024)
        {
            return new { ok = false, message_de = "Ungültige Dateigröße." };
        }

        var sha = Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant();
        var id = Guid.NewGuid().ToString("N")[..12];
        var binPath = Path.Combine(_storeDir, $"{id}.bin");
        var metaPath = Path.Combine(_storeDir, $"{id}.json");
        File.WriteAllBytes(binPath, content);
        var meta = new FirmwarePackageMeta(
            id,
            label,
            sha,
            content.Length,
            DateTime.UtcNow.ToString("o"),
            true,
            notes,
            Flashed: false);
        File.WriteAllText(metaPath, JsonSerializer.Serialize(meta, new JsonSerializerOptions { WriteIndented = true }));
        AppendAudit($"import:{id}:{sha}");
        return new
        {
            ok = true,
            package = meta,
            message_de =
                "Firmwarepaket importiert und gehasht. Flashen ist nicht implementiert / gesperrt."
        };
    }

    public object RequestFlash(string packageId, bool userConfirmFlash)
    {
        AppendAudit($"flash_request:{packageId}:confirm={userConfirmFlash}");
        return new
        {
            ok = false,
            status = 403,
            message_de =
                "Firmware-Flash ist deaktiviert. Keine automatische oder unkontrollierte Firmwareänderung. " +
                "Erst nach gesonderter Freigabe und Laborverfahren."
        };
    }

    public IReadOnlyList<FirmwarePackageMeta> ListImported()
    {
        var list = new List<FirmwarePackageMeta>();
        foreach (var path in Directory.EnumerateFiles(_storeDir, "*.json"))
        {
            try
            {
                var m = JsonSerializer.Deserialize<FirmwarePackageMeta>(File.ReadAllText(path));
                if (m is not null) list.Add(m);
            }
            catch
            {
                // ignore corrupt meta
            }
        }
        return list;
    }

    private void AppendAudit(string line)
    {
        var audit = Path.Combine(_storeDir, "firmware-audit.log");
        File.AppendAllText(audit, $"{DateTime.UtcNow:o}\t{line}{Environment.NewLine}", Encoding.UTF8);
    }
}

public sealed record FirmwarePackageMeta(
    string Id,
    string Label,
    string Sha256,
    int Bytes,
    string ImportedAtUtc,
    bool UserConfirmedRights,
    string? Notes,
    bool Flashed
);
