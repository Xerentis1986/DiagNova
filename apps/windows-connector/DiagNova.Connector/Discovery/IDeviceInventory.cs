namespace DiagNova.Connector.Discovery;

public interface IDeviceInventory
{
    string Name { get; }
    Task<DeviceInventorySnapshot> ScanAsync(CancellationToken cancellationToken = default);
}

public interface IComPortScanner
{
    IReadOnlyList<DiscoveredDevice> ListComPorts();
}

public interface IBluetoothScanner
{
    Task<IReadOnlyList<DiscoveredDevice>> ListPairedAsync(CancellationToken cancellationToken = default);
    string LimitationDe { get; }
}

public interface IUsbScanner
{
    IReadOnlyList<DiscoveredDevice> ListUsbDevices();
    string LimitationDe { get; }
}
