using DiagNova.Connector.Logging;

namespace DiagNova.Connector.Adapters.DelphiCdp;

/// <summary>
/// CDP+-Sitzung: nur Allowlist-Geräteabfragen standardmäßig.
/// Fahrzeug-/Relais-Befehle erfordern explizites Release-Flag (Default: aus).
/// </summary>
public sealed class CdpSession : IAsyncDisposable
{
    private readonly ICdpTransport _transport;
    private readonly DiagnosticProtocolLog _log;
    private readonly bool _allowVehicleCommands;

    public CdpSession(
        ICdpTransport transport,
        DiagnosticProtocolLog log,
        bool allowVehicleCommands = false)
    {
        _transport = transport;
        _log = log;
        _allowVehicleCommands = allowVehicleCommands;
    }

    public bool VehicleCommandsEnabled => _allowVehicleCommands;
    public bool IsSimulator => _transport.IsSimulator;

    public async Task OpenAsync(CancellationToken ct = default)
    {
        await _transport.OpenAsync(ct).ConfigureAwait(false);
        _log.Info("cdp", "Transport geöffnet", _transport.Name);
    }

    public async Task<CdpIdentity> ReadIdentityAsync(CancellationToken ct = default)
    {
        var serial = await QuerySafeAsync("200", ct).ConfigureAwait(false);
        var fw = await QuerySafeAsync("201", ct).ConfigureAwait(false);
        var name = await QuerySafeAsync("20A", ct).ConfigureAwait(false);
        var battRaw = await QuerySafeAsync("203", ct).ConfigureAwait(false);

        CdpProtocol.TryParseBatteryVolts(battRaw.Raw, out var volts);
        var serialPayload = serial.Payload ?? "";
        return new CdpIdentity(
            DeviceName: name.Payload ?? name.Raw,
            SerialPayload: serialPayload,
            FirmwarePayload: fw.Payload ?? fw.Raw,
            BatteryVolts: volts > 0 ? volts : null,
            SerialMatchesOperatorFamily: CdpCompatibility.SerialLooksLikeDocumentedFamily(serialPayload),
            HardwareTested: false,
            DataSource: _transport.IsSimulator ? "simulated" : "live_unverified",
            MessageDe: _transport.IsSimulator
                ? "Identität aus Fake-Transport (dokumentierte Beispielantworten)."
                : "Identität gelesen – Hardware noch nicht freigegeben/laborgeprüft."
        );
    }

    public async Task<CdpResponse> QuerySafeAsync(string commandCode, CancellationToken ct = default)
    {
        if (!CdpProtocol.IsSafeDeviceRead(commandCode))
        {
            _log.Warn("cdp", "Nicht-Allowlist-Befehl blockiert", commandCode);
            throw new InvalidOperationException(
                $"Befehl '{commandCode}' ist kein freigegebener Geräte-Lesebefehl.");
        }

        return await ExchangeAsync(commandCode, Array.Empty<string>(), ct).ConfigureAwait(false);
    }

    /// <summary>
    /// Fahrzeug-/CAN-/Relais-Pfad – standardmäßig 403-äquivalent Exception.
    /// </summary>
    public Task<CdpResponse> SendVehicleCommandAsync(
        string commandCode,
        string[] args,
        CancellationToken ct = default)
    {
        if (!_allowVehicleCommands || CdpProtocol.IsVehicleOrRelayCommand(commandCode))
        {
            if (!_allowVehicleCommands)
            {
                _log.Warn("cdp", "Fahrzeugbefehl gesperrt (keine Freigabe)", commandCode);
                throw new InvalidOperationException(
                    "Fahrzeug-/Relais-/CAN-Befehle sind deaktiviert. " +
                    "Keine ungeprüfte Pin-Umschaltung, kein TesterPresent, kein ECU-Schreiben.");
            }
        }

        // Selbst mit Flag: nur explizit – zusätzliche Soft-Sperre für bekannte Gefahrencodes
        if (CdpProtocol.IsVehicleOrRelayCommand(commandCode) && !_allowVehicleCommands)
        {
            throw new InvalidOperationException("Relais/CAN gesperrt");
        }

        // Mit Freigabe immer noch keine Auto-Firmware
        if (commandCode.StartsWith("918", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("Self-Test/Firmware-Pfade nicht freigegeben.");
        }

        return ExchangeAsync(commandCode, args, ct);
    }

    private async Task<CdpResponse> ExchangeAsync(
        string commandCode,
        string[] args,
        CancellationToken ct)
    {
        var framed = CdpProtocol.EncodeCommand(commandCode, args);
        _log.Info("cdp", "TX", framed.Replace("\r", "\\r"));
        await _transport.WriteAsciiAsync(framed, ct).ConfigureAwait(false);
        var raw = await _transport.ReadAsciiFrameAsync(TimeSpan.FromSeconds(3), ct).ConfigureAwait(false);
        _log.Info("cdp", "RX", raw.Replace("\r", "\\r"));
        return CdpProtocol.ParseResponse(raw);
    }

    public async ValueTask DisposeAsync()
    {
        await _transport.CloseAsync().ConfigureAwait(false);
        await _transport.DisposeAsync().ConfigureAwait(false);
    }
}

public sealed record CdpIdentity(
    string DeviceName,
    string SerialPayload,
    string FirmwarePayload,
    double? BatteryVolts,
    bool SerialMatchesOperatorFamily,
    bool HardwareTested,
    string DataSource,
    string MessageDe
);
