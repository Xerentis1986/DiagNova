using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Transport;

namespace DiagNova.Connector.Adapters;

public sealed class AdapterConnectionManager : IDiagnosticAdapter
{
    private readonly ISerialTransportFactory _factory;
    private readonly Elm327DriverPrep _elmPrep;
    private readonly DiagnosticProtocolLog _log;
    private readonly object _gate = new();

    private ISerialTransport? _transport;
    private IDiagnosticAdapter _active = new StubDiagnosticAdapter();
    private string? _selectedDeviceId;
    private bool _adapterLinkUp;
    private Elm327PrepResult? _lastPrep;

    public AdapterConnectionManager(
        ISerialTransportFactory factory,
        Elm327DriverPrep elmPrep,
        DiagnosticProtocolLog log)
    {
        _factory = factory;
        _elmPrep = elmPrep;
        _log = log;
    }

    public string Name => _active.Name;
    public string DataSource => _active.DataSource;
    public bool IsSimulator => _active.IsSimulator;

    public AdapterStatus GetStatus()
    {
        lock (_gate)
        {
            var baseStatus = _active.GetStatus();
            if (_active.IsSimulator)
            {
                return baseStatus;
            }

            return new AdapterStatus(
                AdapterConnected: _adapterLinkUp && (_transport?.IsOpen == true),
                VehicleConnected: false, // Phase 03: bewusst nie true
                Mode: _adapterLinkUp ? "adapter-link" : baseStatus.Mode,
                MessageDe: _adapterLinkUp
                    ? "Adapter-Link aktiv – Fahrzeugverbindung in Phase 03 deaktiviert (keine OBD-Befehle)."
                    : baseStatus.MessageDe,
                PortName: _transport?.PortName ?? baseStatus.PortName,
                TransportName: _transport?.Name ?? baseStatus.TransportName,
                LastHeartbeat: DateTimeOffset.UtcNow,
                LimitationsDe: MergeLimitations(baseStatus.LimitationsDe)
            );
        }
    }

    public object GetExtendedStatus()
    {
        var status = GetStatus();
        return new
        {
            adapter = status,
            selected_device_id = _selectedDeviceId,
            last_elm_prep = _lastPrep is null ? null : new
            {
                success = _lastPrep.Success,
                message_de = _lastPrep.MessageDe,
                exchanges = _lastPrep.Exchanges.Select(e => new
                {
                    command = e.Command,
                    success = e.Success,
                    // Rohantwort gekürzt – kein Fahrzeug-Payload
                    raw_preview = e.RawResponse.Length > 80 ? e.RawResponse[..80] + "…" : e.RawResponse
                })
            },
            separation = new
            {
                adapter_connection = status.AdapterConnected,
                vehicle_connection = status.VehicleConnected,
                note_de = "Adapter- und Fahrzeugverbindung werden getrennt angezeigt."
            }
        };
    }

    public async Task<object> SelectSimulatorAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        await DisconnectInternalAsync().ConfigureAwait(false);
        lock (_gate)
        {
            _active = new SimulatorAdapter();
            _selectedDeviceId = "sim:local";
            _adapterLinkUp = true;
            _lastPrep = null;
        }
        _log.Info("connection", "Simulator ausgewählt (separater Pfad).");
        return GetExtendedStatus();
    }

    public async Task<object> ConnectFakeAsync(CancellationToken cancellationToken = default)
    {
        return await ConnectTransportAsync(
            deviceId: "fake:COM99",
            transportKind: "fake",
            portName: "COM99",
            runAtInit: true,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<object> ConnectComAsync(
        string portName,
        string transportKind = "system",
        bool runAtInit = false,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(portName))
        {
            throw new ArgumentException("PortName erforderlich.", nameof(portName));
        }

        // Echte System-Ports: nur öffnen/schließen in Phase 03; AT-Init nur auf Fake oder explizit.
        return await ConnectTransportAsync(
            deviceId: $"com:{portName}",
            transportKind: transportKind,
            portName: portName,
            runAtInit: runAtInit && transportKind.Equals("fake", StringComparison.OrdinalIgnoreCase),
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<object> DisconnectAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        await DisconnectInternalAsync().ConfigureAwait(false);
        lock (_gate)
        {
            _active = new StubDiagnosticAdapter();
            _selectedDeviceId = null;
            _adapterLinkUp = false;
            _lastPrep = null;
        }
        _log.Info("connection", "Adapter getrennt.");
        return GetExtendedStatus();
    }

    private async Task<object> ConnectTransportAsync(
        string deviceId,
        string transportKind,
        string portName,
        bool runAtInit,
        CancellationToken cancellationToken)
    {
        await DisconnectInternalAsync().ConfigureAwait(false);

        var transport = _factory.Create(transportKind);
        try
        {
            await transport.OpenAsync(new SerialTransportOptions
            {
                PortName = portName,
                BaudRate = 38400,
                ExclusiveAccess = true
            }, cancellationToken).ConfigureAwait(false);

            Elm327PrepResult? prep = null;
            if (runAtInit)
            {
                prep = await _elmPrep.RunAtInitAsync(transport, TimeSpan.FromSeconds(2), cancellationToken)
                    .ConfigureAwait(false);
            }

            lock (_gate)
            {
                _transport = transport;
                _selectedDeviceId = deviceId;
                _adapterLinkUp = true;
                _lastPrep = prep;
                _active = new LinkedSerialAdapter(transport.Name, portName, transportKind);
            }

            _log.Info("connection", $"Transport geöffnet: {transportKind} / {portName}", deviceId);
            return GetExtendedStatus();
        }
        catch
        {
            await transport.DisposeAsync().ConfigureAwait(false);
            throw;
        }
    }

    private async Task DisconnectInternalAsync()
    {
        ISerialTransport? transport;
        lock (_gate)
        {
            transport = _transport;
            _transport = null;
            _adapterLinkUp = false;
        }
        if (transport is not null)
        {
            try
            {
                await transport.CloseAsync().ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                _log.Warn("connection", "Close-Fehler", ex.Message);
            }
            await transport.DisposeAsync().ConfigureAwait(false);
        }
    }

    private IReadOnlyList<string> MergeLimitations(IReadOnlyList<string> baseLimitations)
    {
        var list = new List<string>(baseLimitations)
        {
            "Fahrzeugverbindung in Phase 03 immer false – keine OBD-Befehle.",
            "Delphi/Autocom nicht angebunden (keine dokumentierte Schnittstelle).",
            "Vgate/ELM327: nur Treiber-Vorbereitung; SPP-Variante ungeprüft."
        };
        return list;
    }

    private sealed class LinkedSerialAdapter : IDiagnosticAdapter
    {
        private readonly string _transportName;
        private readonly string _portName;
        private readonly string _kind;

        public LinkedSerialAdapter(string transportName, string portName, string kind)
        {
            _transportName = transportName;
            _portName = portName;
            _kind = kind;
        }

        public string Name => $"Serial:{_portName}";
        public string DataSource => _kind.Equals("fake", StringComparison.OrdinalIgnoreCase) ? "simulated" : "hardware-link-only";
        public bool IsSimulator => false;

        public AdapterStatus GetStatus() => new(
            AdapterConnected: true,
            VehicleConnected: false,
            Mode: "adapter-link",
            MessageDe: "Serieller Adapter-Link – keine Fahrzeugbefehle.",
            PortName: _portName,
            TransportName: _transportName,
            LastHeartbeat: DateTimeOffset.UtcNow,
            LimitationsDe: Array.Empty<string>()
        );
    }
}
