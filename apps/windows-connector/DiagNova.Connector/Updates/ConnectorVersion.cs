namespace DiagNova.Connector.Updates;

/// <summary>
/// Connector-Version und Update-Metadaten (getrennt von Diagnosedaten).
/// Phase 15: Security-Hinweise; Loopback/Auth unverändert.
/// </summary>
public static class ConnectorVersion
{
    public const string Version = "0.15.0";
    public const string Channel = "stable-fixture";
    public const string PhaseNoteDe =
        "Phase 15: Security/Datenschutz. Loopback-only, Pairing-Token, keine Remote-Rohbefehle. "
        + "Produktive Auto-Updates ohne Signaturzertifikat gesperrt.";
}
