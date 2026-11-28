using System.Runtime.InteropServices;
using DiagNova.Connector.Adapters.DelphiCdp;
using DiagNova.Connector.Discovery;
using DiagNova.Connector.Logging;

Console.WriteLine("DiagNova CDP+/Delphi Hardware-Probe (read-only)");
Console.WriteLine("Keine Firmwareänderung, keine Fahrzeugbefehle, kein Relais.");
Console.WriteLine($"OS: {RuntimeInformation.OSDescription}");
Console.WriteLine();

Console.WriteLine("=== Dokumentierte USB-Ziel-ID (Forschung) ===");
Console.WriteLine($"VID:PID = {CdpProtocol.DocumentedVendorId:X4}:{CdpProtocol.DocumentedProductId:X4}");
Console.WriteLine();

var log = new DiagnosticProtocolLog();
var com = new ComPortScanner();
var usb = new UsbScanner();
var bt = new BluetoothScanner();
var inventory = new CompositeDeviceInventory(com, bt, usb);
var snap = await inventory.ScanAsync();

Console.WriteLine("=== Geräteinventar (read-only) ===");
foreach (var d in snap.Devices)
{
    Console.WriteLine($"- [{d.Kind}] {d.DisplayName} port={d.PortName} vendor={d.VendorHint} id={d.Id}");
}
Console.WriteLine("Limitations:");
foreach (var l in snap.LimitationsDe) Console.WriteLine($"  · {l}");
Console.WriteLine();

Console.WriteLine("=== Simulator-Identität (dokumentierte Beispielantworten) ===");
var svc = new DelphiCdpAdapterService(log, inventory);
var sim = await svc.IdentifySimulatedAsync();
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(sim, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine();

Console.WriteLine("=== Live-FTDI Open (erwartet: ehrlicher Fail ohne HW/D2XX) ===");
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(svc.TryOpenLive(), new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine();

Console.WriteLine("=== Kompatibilität ===");
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(CdpCompatibility.Matrix(), new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine();
Console.WriteLine("Fertig. hardware_tested=false. Mit Adapter auf Windows: VID/PID + *200/*201 prüfen.");
