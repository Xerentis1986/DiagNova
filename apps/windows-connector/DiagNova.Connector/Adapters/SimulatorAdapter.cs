namespace DiagNova.Connector.Adapters;

/// <summary>
/// Separater Simulator-Adapter (kein echter Fahrzeugbus).
/// data_source immer "simulated".
/// </summary>
public sealed class SimulatorAdapter : IDiagnosticAdapter
{
    public string Name => "DiagNova Local Simulator";
    public string DataSource => "simulated";
    public bool IsSimulator => true;

    public AdapterStatus GetStatus() => new(
        AdapterConnected: true,
        VehicleConnected: false,
        Mode: "simulator",
        MessageDe: "Simulator-Pfad – keine Hardware. OBD-Antworten aus dokumentierten Testvektoren (simulated).",
        PortName: null,
        TransportName: "simulator",
        LastHeartbeat: DateTimeOffset.UtcNow,
        LimitationsDe: new[]
        {
            "Rein simuliert – keine Hardware.",
            "Keine Live-Freigabe ohne Hardwaretest."
        }
    );
}
