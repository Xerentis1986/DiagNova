namespace DiagNova.Connector.Adapters;

/// <summary>
/// Vertrag für lokale Diagnoseadapter.
/// Implementierungen dürfen in Phase C+ echte OBD-Kommunikation hinzufügen –
/// dieses Skelett enthält KEINE Fahrzeugbefehle.
/// </summary>
public interface IDiagnosticAdapter
{
    string Name { get; }
    string DataSource { get; }
    AdapterStatus GetStatus();
}

public sealed record AdapterStatus(
    bool Connected,
    string Mode,
    string MessageDe,
    DateTimeOffset? LastHeartbeat
);
