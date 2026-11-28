namespace DiagNova.Connector.Adapters;

/// <summary>
/// Stub ohne Hardwarezugriff und ohne Fahrzeugbefehle.
/// </summary>
public sealed class StubDiagnosticAdapter : IDiagnosticAdapter
{
    public string Name => "StubDiagnosticAdapter";
    public string DataSource => "none";
    public bool IsSimulator => false;

    public AdapterStatus GetStatus() => new(
        AdapterConnected: false,
        VehicleConnected: false,
        Mode: "stub",
        MessageDe: "Stub aktiv – keine COM/Bluetooth-Verbindung, keine Fahrzeugbefehle.",
        PortName: null,
        TransportName: null,
        LastHeartbeat: DateTimeOffset.UtcNow,
        LimitationsDe: new[] { "Kein Transport gewählt." }
    );
}
