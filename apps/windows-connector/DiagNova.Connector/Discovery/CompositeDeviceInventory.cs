using System.Runtime.InteropServices;

namespace DiagNova.Connector.Discovery;

public sealed class CompositeDeviceInventory : IDeviceInventory
{
    private readonly IComPortScanner _com;
    private readonly IBluetoothScanner _bluetooth;
    private readonly IUsbScanner _usb;

    public CompositeDeviceInventory(
        IComPortScanner com,
        IBluetoothScanner bluetooth,
        IUsbScanner usb)
    {
        _com = com;
        _bluetooth = bluetooth;
        _usb = usb;
    }

    public string Name => "CompositeDeviceInventory";

    public async Task<DeviceInventorySnapshot> ScanAsync(CancellationToken cancellationToken = default)
    {
        var devices = new List<DiscoveredDevice>
        {
            new(
                Id: "sim:local",
                Kind: DeviceKind.Simulator,
                DisplayName: "DiagNova Local Simulator",
                PortName: null,
                Address: null,
                VendorHint: "diagnova",
                IsPaired: true,
                IsAvailable: true,
                Source: "built-in",
                NotesDe: "Separater Simulator – keine Hardware, keine echten Fahrzeugbefehle."
            )
        };

        devices.AddRange(_com.ListComPorts());
        devices.AddRange(_usb.ListUsbDevices());
        devices.AddRange(await _bluetooth.ListPairedAsync(cancellationToken).ConfigureAwait(false));

        var limitations = new List<string>
        {
            _bluetooth.LimitationDe,
            _usb.LimitationDe,
            "Delphi/Autocom: keine dokumentierte öffentliche Schnittstelle im Repo – Anbindung deaktiviert (siehe docs/delphi-autocom-interface.md).",
            "Vgate vLinker MC+: Windows-SPP-Variante und Herstellerdokumentation nicht verifiziert – nur ELM327-Treiber-Vorbereitung (docs/vgate-elm327-prep.md).",
            "Phase 03 sendet keine OBD-/Fahrzeugdiagnosebefehle."
        };

        return new DeviceInventorySnapshot(
            CapturedAt: DateTimeOffset.UtcNow,
            Platform: RuntimeInformation.OSDescription,
            Devices: devices,
            LimitationsDe: limitations
        );
    }
}
