using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
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
    private ObdSession? _obdSession;
    private bool _vehicleLinked;

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
    public ObdSession? CurrentSession
    {
        get { lock (_gate) return _obdSession; }
    }

    public AdapterStatus GetStatus()
    {
        lock (_gate)
        {
            var baseStatus = _active.GetStatus();
            if (_active.IsSimulator && _obdSession is null)
            {
                return baseStatus;
            }

            return new AdapterStatus(
                AdapterConnected: _adapterLinkUp && (_transport?.IsOpen == true || _active.IsSimulator),
                VehicleConnected: _vehicleLinked,
                Mode: _vehicleLinked ? "vehicle-link" : (_adapterLinkUp ? "adapter-link" : baseStatus.Mode),
                MessageDe: _vehicleLinked
                    ? $"Fahrzeugverbindung aktiv ({DataSource})."
                    : (_adapterLinkUp
                        ? "Adapter-Link aktiv – OBD-Init noch nicht erfolgreich oder nicht ausgeführt."
                        : baseStatus.MessageDe),
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
        ObdSession? session;
        lock (_gate) session = _obdSession;
        return new
        {
            adapter = status,
            selected_device_id = _selectedDeviceId,
            data_source = DataSource,
            is_simulator = IsSimulator,
            last_elm_prep = _lastPrep is null ? null : new
            {
                success = _lastPrep.Success,
                message_de = _lastPrep.MessageDe,
                exchanges = _lastPrep.Exchanges.Select(e => new
                {
                    command = e.Command,
                    success = e.Success,
                    raw_preview = e.RawResponse.Length > 80 ? e.RawResponse[..80] + "…" : e.RawResponse
                })
            },
            obd = session is null ? null : new
            {
                vehicle_linked = session.VehicleLinked,
                protocol_name = session.ProtocolName,
                protocol_number = session.ProtocolNumber,
                supported_pid_count = session.SupportedPids.Count
            },
            separation = new
            {
                adapter_connection = status.AdapterConnected,
                vehicle_connection = status.VehicleConnected,
                note_de = "Adapter- und Fahrzeugverbindung werden getrennt angezeigt. Live vs. Demo strikt getrennt."
            }
        };
    }

    public async Task<object> SelectSimulatorAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        await DisconnectInternalAsync().ConfigureAwait(false);

        // Simulator nutzt Fake-Transport mit OBD-Antwortvektoren
        var transport = _factory.Create("fake");
        await transport.OpenAsync(new SerialTransportOptions
        {
            PortName = "SIM",
            BaudRate = 38400,
            ExclusiveAccess = true
        }, cancellationToken).ConfigureAwait(false);

        var session = new ObdSession(transport, _log, isSimulator: true, dataSource: "simulated");
        lock (_gate)
        {
            _transport = transport;
            _active = new SimulatorAdapter();
            _selectedDeviceId = "sim:local";
            _adapterLinkUp = true;
            _lastPrep = null;
            _obdSession = session;
            _vehicleLinked = false;
        }
        _log.Info("connection", "Simulator ausgewählt (separater Pfad, data_source=simulated).");
        return GetExtendedStatus();
    }

    public async Task<object> ConnectFakeAsync(CancellationToken cancellationToken = default)
    {
        return await ConnectTransportAsync(
            deviceId: "fake:COM99",
            transportKind: "fake",
            portName: "COM99",
            runAtInit: true,
            dataSource: "simulated",
            isSimulator: true,
            cancellationToken).ConfigureAwait(false);
    }

    public async Task<object> ConnectComAsync(
        string portName,
        string transportKind = "system",
        bool runAtInit = true,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(portName))
        {
            throw new ArgumentException("PortName erforderlich.", nameof(portName));
        }

        var isFake = transportKind.Equals("fake", StringComparison.OrdinalIgnoreCase);
        return await ConnectTransportAsync(
            deviceId: $"com:{portName}",
            transportKind: transportKind,
            portName: portName,
            runAtInit: runAtInit,
            dataSource: isFake ? "simulated" : "live",
            isSimulator: isFake,
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
            _obdSession = null;
            _vehicleLinked = false;
        }
        _log.Info("connection", "Adapter getrennt.");
        return GetExtendedStatus();
    }

    public async Task<object> InitObdAsync(CancellationToken cancellationToken = default)
    {
        var session = RequireSession();
        var result = await session.InitializeAsync(cancellationToken).ConfigureAwait(false);
        lock (_gate)
        {
            _vehicleLinked = session.VehicleLinked;
        }
        return result;
    }

    public Task<object> ReadLiveAsync(CancellationToken ct = default) =>
        RequireSession().ReadLiveAsync(ct);

    public Task<object> ReadDtcsAsync(CancellationToken ct = default) =>
        RequireSession().ReadDtcsAsync(ct);

    public Task<object> ReadFreezeFrameAsync(CancellationToken ct = default) =>
        RequireSession().ReadFreezeFrameAsync(ct);

    public Task<object> ReadReadinessAsync(CancellationToken ct = default) =>
        RequireSession().ReadReadinessAsync(ct);

    public Task<object> ReadVinAsync(CancellationToken ct = default) =>
        RequireSession().ReadVinAsync(ct);

    public Task<object> ListEcusAsync(bool refresh = true, CancellationToken ct = default) =>
        RequireSession().ListEcusAsync(refresh, ct);

    public Task<object> ClearDtcsAsync(ClearApproval approval, CancellationToken ct = default) =>
        RequireSession().ClearDtcsAsync(approval, ct);

    private ObdSession RequireSession()
    {
        lock (_gate)
        {
            if (_obdSession is null || _transport?.IsOpen != true)
            {
                throw new InvalidOperationException(
                    "Kein aktiver OBD-Transport – zuerst Adapter verbinden (Fake/COM/Simulator).");
            }
            return _obdSession;
        }
    }

    private async Task<object> ConnectTransportAsync(
        string deviceId,
        string transportKind,
        string portName,
        bool runAtInit,
        string dataSource,
        bool isSimulator,
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

            var session = new ObdSession(transport, _log, isSimulator, dataSource);

            lock (_gate)
            {
                _transport = transport;
                _selectedDeviceId = deviceId;
                _adapterLinkUp = true;
                _lastPrep = prep;
                _obdSession = session;
                _vehicleLinked = false;
                _active = new LinkedSerialAdapter(transport.Name, portName, transportKind, dataSource, isSimulator);
            }

            _log.Info("connection", $"Transport geöffnet: {transportKind} / {portName} ({dataSource})", deviceId);
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
            _obdSession = null;
            _vehicleLinked = false;
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
            "Echte Hardwarefreigabe ausstehend (BLK-HW / BLK-ADAPTER).",
            "Delphi/Autocom nicht angebunden (keine dokumentierte Schnittstelle).",
            "Vgate/ELM327: SPP-Variante ungeprüft – Fake/Simulator für Parser-Tests.",
            "Live vs. simulated strikt getrennt (data_source).",
            "Mode 04 nur mit Freigabe-Token; permanente DTCs nicht löschbar."
        };
        return list;
    }

    private sealed class LinkedSerialAdapter : IDiagnosticAdapter
    {
        private readonly string _transportName;
        private readonly string _portName;
        private readonly string _kind;
        private readonly string _dataSource;
        private readonly bool _isSimulator;

        public LinkedSerialAdapter(string transportName, string portName, string kind, string dataSource, bool isSimulator)
        {
            _transportName = transportName;
            _portName = portName;
            _kind = kind;
            _dataSource = dataSource;
            _isSimulator = isSimulator;
        }

        public string Name => $"Serial:{_portName}";
        public string DataSource => _dataSource;
        public bool IsSimulator => _isSimulator;

        public AdapterStatus GetStatus() => new(
            AdapterConnected: true,
            VehicleConnected: false,
            Mode: "adapter-link",
            MessageDe: $"Serieller Adapter-Link ({_dataSource}).",
            PortName: _portName,
            TransportName: _transportName,
            LastHeartbeat: DateTimeOffset.UtcNow,
            LimitationsDe: Array.Empty<string>()
        );
    }
}
