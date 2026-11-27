using System.IO.Ports;
using System.Runtime.InteropServices;

namespace DiagNova.Connector.Discovery;

/// <summary>
/// COM-/serielles Port-Inventar über <see cref="SerialPort.GetPortNames"/>.
/// Keine Portöffnung, keine Fahrzeugbefehle.
/// </summary>
public sealed class ComPortScanner : IComPortScanner
{
    public IReadOnlyList<DiscoveredDevice> ListComPorts()
    {
        string[] names;
        try
        {
            names = SerialPort.GetPortNames();
        }
        catch (Exception ex)
        {
            return new[]
            {
                new DiscoveredDevice(
                    Id: "com:error",
                    Kind: DeviceKind.ComPort,
                    DisplayName: "COM-Scan fehlgeschlagen",
                    PortName: null,
                    Address: null,
                    VendorHint: null,
                    IsPaired: false,
                    IsAvailable: false,
                    Source: "System.IO.Ports",
                    NotesDe: $"COM-Inventar nicht lesbar: {ex.GetType().Name}"
                )
            };
        }

        Array.Sort(names, StringComparer.OrdinalIgnoreCase);
        return names.Select(name => new DiscoveredDevice(
            Id: $"com:{name}",
            Kind: DeviceKind.ComPort,
            DisplayName: name,
            PortName: name,
            Address: null,
            VendorHint: GuessVendorHint(name),
            IsPaired: false,
            IsAvailable: true,
            Source: "System.IO.Ports.SerialPort.GetPortNames",
            NotesDe: "Nur Inventar – Port nicht geöffnet."
        )).ToList();
    }

    private static string? GuessVendorHint(string portName)
    {
        // Heuristik ohne Hardwarezugriff – keine Garantie.
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) &&
            portName.StartsWith("COM", StringComparison.OrdinalIgnoreCase))
        {
            return "windows-com";
        }
        if (portName.Contains("usb", StringComparison.OrdinalIgnoreCase) ||
            portName.Contains("ttyUSB", StringComparison.OrdinalIgnoreCase) ||
            portName.Contains("ttyACM", StringComparison.OrdinalIgnoreCase))
        {
            return "usb-serial";
        }
        return null;
    }
}
