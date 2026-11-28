using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;
using DiagNova.Connector.Obd;
using DiagNova.Connector.Transport;

namespace DiagNova.Connector.Adapters.Vgate;

/// <summary>
/// Vgate iCar Pro 2S – Bluetooth OBD2, Hersteller: ELM327 V2.3 kompatibel.
/// Preisband Recherche ~38–42€ (≤100€). Live-HW in dieser Umgebung NOT TESTED.
/// Nutzt nur dokumentierte AT/OBD-II-Befehle (ObdCommandAllowlist) – kein erfundenes Protokoll.
/// </summary>
public sealed class VgateIcarPro2sAdapterService
{
    public const string AdapterId = "vgate-icar-pro-2s";
    public const string ExactProductName = "Vgate iCar Pro 2S";
    public const string Manufacturer = "Vgate Direct";

    private readonly IDeviceInventory _inventory;
    private readonly ISerialTransportFactory _transportFactory;
    private readonly Elm327DriverPrep _prep;
    private readonly DiagnosticProtocolLog _log;

    public VgateIcarPro2sAdapterService(
        IDeviceInventory inventory,
        ISerialTransportFactory transportFactory,
        Elm327DriverPrep prep,
        DiagnosticProtocolLog log)
    {
        _inventory = inventory;
        _transportFactory = transportFactory;
        _prep = prep;
        _log = log;
    }

    public object Status() => new
    {
        adapter_id = AdapterId,
        product_exact_de = ExactProductName,
        manufacturer = Manufacturer,
        bluetooth = "5.2",
        elm327_version_claimed = "V2.3",
        elm327_compatibility_evidence_de =
            "Hersteller/Amazon/Fachhandel: voll ELM327-kompatibel; AT-Befehlssatz. " +
            "Schnittstelle damit = dokumentiertes ELM327/OBD-II – kein proprietäres Rätselraten.",
        price_band_eur = "ca. 38–42 (Recherche 2026-11, ≤100€)",
        hardware_tested = false,
        vehicle_tested = false,
        data_source_policy = "live nur mit echtem Port; sonst ehrlicher Fail / Fake separat",
        message_de =
            "Treiberpfad bereit (ELM327 AT over COM/BT-SPP). Physischer Adapter hier nicht angeschlossen."
    };

    public object Research() => new
    {
        product = ExactProductName,
        brand = "Vgate",
        max_budget_eur = 100,
        sources = new[]
        {
            "https://www.amazon.de/dp/B0D4Y77CYX",
            "https://www.idealo.de/preisvergleich/OffersOfProduct/208804290_-icar-pro-2s-obd2-vgate.html",
            "https://www.nabennerd24.de/products/icar-pro-2s-obd-2-diagnoseadapter"
        },
        interface_name = "ELM327 AT over Bluetooth RFCOMM / virtuellem COM",
        docs_path = "docs/DIAGNOVA_PHASE25_BT_ADAPTER_CHOICE.md"
    };

    /// <summary>
    /// Nichtinvasive Inventur: BT-/COM-Kandidaten mit Vgate/iCar/ELM-Hinweis.
    /// </summary>
    public async Task<object> InventoryProbeAsync(CancellationToken ct = default)
    {
        var snap = await _inventory.ScanAsync(ct).ConfigureAwait(false);
        var candidates = snap.Devices
            .Where(d =>
            {
                var blob = $"{d.DisplayName}|{d.VendorHint}|{d.PortName}|{d.Kind}".ToLowerInvariant();
                return blob.Contains("vgate")
                       || blob.Contains("icar")
                       || blob.Contains("elm")
                       || blob.Contains("obd")
                       || d.Kind.ToString().Contains("Bluetooth", StringComparison.OrdinalIgnoreCase)
                       || d.Kind.ToString().Contains("Com", StringComparison.OrdinalIgnoreCase);
            })
            .Select(d => new
            {
                d.Id,
                kind = d.Kind.ToString(),
                d.DisplayName,
                d.PortName,
                d.VendorHint
            })
            .ToArray();

        return new
        {
            ok = true,
            adapter_id = AdapterId,
            product = ExactProductName,
            hardware_tested = false,
            vehicle_commands_sent = false,
            candidates,
            limitations_de = snap.LimitationsDe,
            message_de =
                "Inventur nur. Verbindungstest: POST /adapters/vgate-icar-pro-2s/connection-test mit port_name."
        };
    }

    /// <summary>
    /// Optionaler ATZ-Prep auf angegebenem Port (COM/BT-SPP). Ohne Port: ehrlicher Fail.
    /// </summary>
    public async Task<object> ConnectionTestAsync(string? portName, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(portName))
        {
            return new
            {
                ok = false,
                status = "port_required",
                hardware_tested = false,
                message_de =
                    "Kein port_name. Bitte Bluetooth-SPP/COM des Vgate iCar Pro 2S angeben. " +
                    "Kein Fake-Erfolg ohne Port."
            };
        }

        try
        {
            var transport = _transportFactory.Create(
                portName.Equals("COM99", StringComparison.OrdinalIgnoreCase) ||
                portName.Equals("FAKE", StringComparison.OrdinalIgnoreCase)
                    ? "fake"
                    : "system");
            await transport.OpenAsync(new SerialTransportOptions
            {
                PortName = portName,
                BaudRate = 38400,
                ExclusiveAccess = true
            }, ct).ConfigureAwait(false);

            var isFake = portName.Equals("COM99", StringComparison.OrdinalIgnoreCase)
                         || portName.Equals("FAKE", StringComparison.OrdinalIgnoreCase)
                         || portName.Equals("SIM", StringComparison.OrdinalIgnoreCase);
            var prep = await _prep.RunAtInitAsync(transport, TimeSpan.FromSeconds(3), ct).ConfigureAwait(false);
            await transport.DisposeAsync().ConfigureAwait(false);

            return new
            {
                ok = prep.Success,
                status = prep.Success ? (isFake ? "adapter_fake_ok" : "elm_atz_ok") : "elm_atz_failed",
                data_source = isFake ? "adapter_fake" : "live_unverified",
                hardware_tested = prep.Success && !isFake,
                vehicle_tested = false,
                responses = prep.Exchanges,
                message_de = prep.Success
                    ? (isFake
                        ? "Fake-Port: ELM-Prep OK (Test-Double)."
                        : "AT-Prep OK auf Port – Laborverifikation Fahrzeug noch ausstehend.")
                    : prep.MessageDe
            };
        }
        catch (Exception ex)
        {
            _log.Error("vgate", "Connection-Test fehlgeschlagen", ex.Message);
            return new
            {
                ok = false,
                status = "open_failed",
                hardware_tested = false,
                message_de = $"Port {portName} nicht öffnen: {ex.Message}"
            };
        }
    }
}
