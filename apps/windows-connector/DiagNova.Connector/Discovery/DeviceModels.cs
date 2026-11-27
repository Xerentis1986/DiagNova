namespace DiagNova.Connector.Discovery;

public enum DeviceKind
{
    ComPort,
    Usb,
    BluetoothSpp,
    Simulator
}

public sealed record DiscoveredDevice(
    string Id,
    DeviceKind Kind,
    string DisplayName,
    string? PortName,
    string? Address,
    string? VendorHint,
    bool IsPaired,
    bool IsAvailable,
    string Source,
    string NotesDe
);

public sealed record DeviceInventorySnapshot(
    DateTimeOffset CapturedAt,
    string Platform,
    IReadOnlyList<DiscoveredDevice> Devices,
    IReadOnlyList<string> LimitationsDe
);
