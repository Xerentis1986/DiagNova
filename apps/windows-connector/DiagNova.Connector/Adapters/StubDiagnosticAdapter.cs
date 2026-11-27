namespace DiagNova.Connector.Adapters;

/// <summary>
/// Stub ohne Hardwarezugriff und ohne Fahrzeugbefehle.
/// </summary>
public sealed class StubDiagnosticAdapter : IDiagnosticAdapter
{
    public string Name => "StubDiagnosticAdapter";
    public string DataSource => "simulated";

    public AdapterStatus GetStatus() => new(
        Connected: false,
        Mode: "stub",
        MessageDe: "Stub aktiv – keine COM/Bluetooth-Verbindung, keine Fahrzeugbefehle.",
        LastHeartbeat: DateTimeOffset.UtcNow
    );
}
