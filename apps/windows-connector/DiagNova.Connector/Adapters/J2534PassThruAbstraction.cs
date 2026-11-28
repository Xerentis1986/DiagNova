namespace DiagNova.Connector.Adapters;

/// <summary>
/// Modulare J2534-Transportebene (Skelett).
/// Keine DLL-Ladung ohne konkretes Gerät + Lizenzprüfung.
/// Belegt nicht, dass Delphi DS150E J2534 spricht.
/// </summary>
public sealed class J2534PassThruAbstraction
{
    public const string Status = "planned_abstraction";

    public object Describe() => new
    {
        adapter_id = "j2534-passthru",
        status = Status,
        hardware_tested = false,
        dll_bound = false,
        api_surface_planned = new[]
        {
            "PassThruOpen",
            "PassThruClose",
            "PassThruConnect",
            "PassThruDisconnect",
            "PassThruReadMsgs",
            "PassThruWriteMsgs",
            "PassThruStartMsgFilter",
            "PassThruIoctl"
        },
        references = new[]
        {
            "https://automotive.softing.com/standards/programming-interfaces/passthru-sae-j2534/",
            "https://scandoc.de/en/sddev.html"
        },
        message_de =
            "Abstraktion vorbereitet. Keine PassThru-DLL geladen. " +
            "Lizenzbedingungen vor kommerzieller Integration prüfen. " +
            "Delphi-Gerät ≠ automatisch J2534."
    };

    public object TryOpen(string? dllPath)
    {
        return new
        {
            ok = false,
            dll_path = dllPath,
            message_de =
                "PassThruOpen absichtlich nicht ausgeführt – kein Gerät/DLL in dieser Umgebung freigegeben."
        };
    }
}
