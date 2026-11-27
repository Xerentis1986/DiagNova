using System.Runtime.InteropServices;

namespace DiagNova.Connector.Discovery;

/// <summary>
/// USB-Inventar ohne proprietäre Treiber. Unter Linux: /sys/bus/usb/devices.
/// Unter Windows: dokumentierte SetupAPI-Einschränkung – Phase 03 liefert COM-Ports
/// als primäre USB-Serial-Sicht und meldet die Windows-USB-Detailgrenze.
/// </summary>
public sealed class UsbScanner : IUsbScanner
{
    private readonly IReadOnlyList<DiscoveredDevice>? _injected;

    public UsbScanner()
    {
    }

    public UsbScanner(IReadOnlyList<DiscoveredDevice> injected)
    {
        _injected = injected;
    }

    public string LimitationDe
    {
        get
        {
            if (_injected is not null)
            {
                return "Injizierte Testliste – kein echter USB-Bus.";
            }
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                return "Windows-USB-Detailinventar (SetupAPI) in Phase 03 nicht vollständig; USB-Serial erscheint typischerweise als COM-Port.";
            }
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                return "Linux: Lesen von /sys/bus/usb/devices (Vendor/Product falls vorhanden).";
            }
            return "USB-Inventar auf dieser Plattform eingeschränkt.";
        }
    }

    public IReadOnlyList<DiscoveredDevice> ListUsbDevices()
    {
        if (_injected is not null)
        {
            return _injected;
        }

        if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            return ListLinuxSysfs();
        }

        // Windows: bewusst leer + Limitation – COM-Scanner deckt USB-Serial ab.
        return Array.Empty<DiscoveredDevice>();
    }

    private static IReadOnlyList<DiscoveredDevice> ListLinuxSysfs()
    {
        const string root = "/sys/bus/usb/devices";
        if (!Directory.Exists(root))
        {
            return Array.Empty<DiscoveredDevice>();
        }

        var result = new List<DiscoveredDevice>();
        foreach (var dir in Directory.EnumerateDirectories(root))
        {
            var id = Path.GetFileName(dir);
            // Nur echte USB-Devices (z. B. 1-1.2), keine usb1 Host-Controller ohne idVendor.
            var vendorPath = Path.Combine(dir, "idVendor");
            var productPath = Path.Combine(dir, "idProduct");
            if (!File.Exists(vendorPath) || !File.Exists(productPath))
            {
                continue;
            }

            string vendor;
            string product;
            try
            {
                vendor = File.ReadAllText(vendorPath).Trim();
                product = File.ReadAllText(productPath).Trim();
            }
            catch
            {
                continue;
            }

            var productName = TryRead(Path.Combine(dir, "product")) ?? $"USB {vendor}:{product}";
            var manufacturer = TryRead(Path.Combine(dir, "manufacturer"));

            result.Add(new DiscoveredDevice(
                Id: $"usb:{id}",
                Kind: DeviceKind.Usb,
                DisplayName: productName,
                PortName: null,
                Address: id,
                VendorHint: manufacturer ?? $"{vendor}:{product}",
                IsPaired: false,
                IsAvailable: true,
                Source: "sysfs:/sys/bus/usb/devices",
                NotesDe: "Nur Inventar – kein Treiberzugriff, keine Fahrzeugbefehle."
            ));
        }

        return result;
    }

    private static string? TryRead(string path)
    {
        try
        {
            return File.Exists(path) ? File.ReadAllText(path).Trim() : null;
        }
        catch
        {
            return null;
        }
    }
}
