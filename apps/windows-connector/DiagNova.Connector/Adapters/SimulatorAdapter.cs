namespace DiagNova.Connector.Adapters;

/// <summary>
/// Separater Simulator-Adapter (kein serieller Port, keine Fahrzeugbefehle).
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
        MessageDe: "Simulator getrennt vom Hardware-Pfad – Adapter „verbunden“, Fahrzeug nicht (Phase 03 sendet keine OBD-Befehle).",
        PortName: null,
        TransportName: "simulator",
        LastHeartbeat: DateTimeOffset.UtcNow,
        LimitationsDe: new[]
        {
            "Rein simuliert – keine Hardware.",
            "Fahrzeugverbindung bleibt in Phase 03 bewusst false."
        }
    );
}
