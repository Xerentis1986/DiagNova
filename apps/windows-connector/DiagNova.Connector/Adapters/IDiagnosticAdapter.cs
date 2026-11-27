namespace DiagNova.Connector.Adapters;

/// <summary>
/// Vertrag für lokale Diagnoseadapter.
/// Phase 03: Discovery, Transport, Status – KEINE Fahrzeugbefehle.
/// </summary>
public interface IDiagnosticAdapter
{
    string Name { get; }
    string DataSource { get; }
    bool IsSimulator { get; }
    AdapterStatus GetStatus();
}

/// <summary>
/// Getrennte Darstellung: Adapter-Link vs. Fahrzeug-Link.
/// </summary>
public sealed record AdapterStatus(
    bool AdapterConnected,
    bool VehicleConnected,
    string Mode,
    string MessageDe,
    string? PortName,
    string? TransportName,
    DateTimeOffset? LastHeartbeat,
    IReadOnlyList<string> LimitationsDe
)
{
    /// <summary>Abwärtskompatibel: „Connected“ meint Adapter-Link.</summary>
    public bool Connected => AdapterConnected;
}
