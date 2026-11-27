using System.Runtime.InteropServices;

namespace DiagNova.Connector.Discovery;

/// <summary>
/// Gekoppelte Bluetooth-Geräte. Auf Windows: Win32-API (documented).
/// Ohne Windows oder ohne Bluetooth-Stack: leere Liste + dokumentierte Einschränkung.
/// Keine Firmwareänderung, kein SPP-Connect in Phase 03 ohne freigegebene Hardware.
/// </summary>
public sealed class BluetoothScanner : IBluetoothScanner
{
    private readonly IReadOnlyList<DiscoveredDevice>? _injected;

    public BluetoothScanner()
    {
    }

    /// <summary>Test-/Simulator-Konstruktor mit injizierten gekoppelten Geräten.</summary>
    public BluetoothScanner(IReadOnlyList<DiscoveredDevice> injected)
    {
        _injected = injected;
    }

    public string LimitationDe
    {
        get
        {
            if (_injected is not null)
            {
                return "Injizierte Testliste – kein echter Bluetooth-Stack.";
            }
            if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                return "Bluetooth-Inventar nur unter Windows implementiert (Win32 Bluetooth APIs). Diese Laufzeit ist kein Windows.";
            }
            return "Nur gekoppelte Geräte über dokumentierte Win32-APIs; SPP-Verbindung und Vgate-Variante ungeprüft (BLK-ADAPTER).";
        }
    }

    public Task<IReadOnlyList<DiscoveredDevice>> ListPairedAsync(CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (_injected is not null)
        {
            return Task.FromResult(_injected);
        }

        if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return Task.FromResult<IReadOnlyList<DiscoveredDevice>>(Array.Empty<DiscoveredDevice>());
        }

        try
        {
            var devices = WindowsBluetoothNative.TryListPairedDevices();
            return Task.FromResult(devices);
        }
        catch (Exception ex)
        {
            return Task.FromResult<IReadOnlyList<DiscoveredDevice>>(new[]
            {
                new DiscoveredDevice(
                    Id: "bt:error",
                    Kind: DeviceKind.BluetoothSpp,
                    DisplayName: "Bluetooth-Scan fehlgeschlagen",
                    PortName: null,
                    Address: null,
                    VendorHint: null,
                    IsPaired: false,
                    IsAvailable: false,
                    Source: "Win32 Bluetooth",
                    NotesDe: $"Bluetooth-Inventar nicht lesbar: {ex.GetType().Name}: {ex.Message}"
                )
            });
        }
    }
}

/// <summary>
/// Minimaler Wrapper um dokumentierte Win32 Bluetooth Device Discovery.
/// Keine proprietären Delphi/Autocom-APIs.
/// </summary>
internal static class WindowsBluetoothNative
{
    public static IReadOnlyList<DiscoveredDevice> TryListPairedDevices()
    {
        // P/Invoke nur unter Windows; auf anderen Plattformen wird dieser Pfad nicht erreicht.
        // Wir nutzen BluetoothFindFirstDevice / BluetoothFindNextDevice (bthprops).
        var list = new List<DiscoveredDevice>();

        var search = new BLUETOOTH_DEVICE_SEARCH_PARAMS
        {
            dwSize = (uint)Marshal.SizeOf<BLUETOOTH_DEVICE_SEARCH_PARAMS>(),
            fReturnAuthenticated = true,
            fReturnRemembered = true,
            fReturnUnknown = false,
            fReturnConnected = true,
            fIssueInquiry = false,
            cTimeoutMultiplier = 0,
            hRadio = IntPtr.Zero
        };

        var info = new BLUETOOTH_DEVICE_INFO
        {
            dwSize = (uint)Marshal.SizeOf<BLUETOOTH_DEVICE_INFO>()
        };

        var find = BluetoothFindFirstDevice(ref search, ref info);
        if (find == IntPtr.Zero)
        {
            return list;
        }

        try
        {
            do
            {
                var addr = FormatAddress(info.Address);
                var name = info.szName ?? addr;
                list.Add(new DiscoveredDevice(
                    Id: $"bt:{addr}",
                    Kind: DeviceKind.BluetoothSpp,
                    DisplayName: name,
                    PortName: null,
                    Address: addr,
                    VendorHint: GuessObdHint(name),
                    IsPaired: info.fAuthenticated,
                    IsAvailable: info.fConnected || info.fRemembered,
                    Source: "BluetoothFindFirstDevice (bthprops)",
                    NotesDe: "Gekoppelt/gemerkt – SPP-Portzuordnung und Herstellervariante nicht verifiziert."
                ));
            }
            while (BluetoothFindNextDevice(find, ref info));
        }
        finally
        {
            BluetoothFindDeviceClose(find);
        }

        return list;
    }

    private static string? GuessObdHint(string name)
    {
        var n = name.ToLowerInvariant();
        if (n.Contains("vgate") || n.Contains("vlinker") || n.Contains("obd") || n.Contains("elm"))
        {
            return "possible-obd-adapter";
        }
        return null;
    }

    private static string FormatAddress(ulong address)
    {
        // Bluetooth-Adresse als 48-Bit, Anzeige XX:XX:XX:XX:XX:XX
        var bytes = BitConverter.GetBytes(address);
        if (BitConverter.IsLittleEndian)
        {
            return string.Join(':', bytes.Take(6).Reverse().Select(b => b.ToString("X2")));
        }
        return string.Join(':', bytes.Skip(2).Take(6).Select(b => b.ToString("X2")));
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct BLUETOOTH_DEVICE_SEARCH_PARAMS
    {
        public uint dwSize;
        [MarshalAs(UnmanagedType.Bool)] public bool fReturnAuthenticated;
        [MarshalAs(UnmanagedType.Bool)] public bool fReturnRemembered;
        [MarshalAs(UnmanagedType.Bool)] public bool fReturnUnknown;
        [MarshalAs(UnmanagedType.Bool)] public bool fReturnConnected;
        [MarshalAs(UnmanagedType.Bool)] public bool fIssueInquiry;
        public byte cTimeoutMultiplier;
        public IntPtr hRadio;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct BLUETOOTH_DEVICE_INFO
    {
        public uint dwSize;
        public ulong Address;
        public uint ulClassofDevice;
        [MarshalAs(UnmanagedType.Bool)] public bool fConnected;
        [MarshalAs(UnmanagedType.Bool)] public bool fRemembered;
        [MarshalAs(UnmanagedType.Bool)] public bool fAuthenticated;
        public SYSTEMTIME stLastSeen;
        public SYSTEMTIME stLastUsed;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 248)]
        public string szName;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct SYSTEMTIME
    {
        public ushort wYear, wMonth, wDayOfWeek, wDay, wHour, wMinute, wSecond, wMilliseconds;
    }

    [DllImport("bthprops.cpl", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr BluetoothFindFirstDevice(
        ref BLUETOOTH_DEVICE_SEARCH_PARAMS pbtsp,
        ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("bthprops.cpl", SetLastError = true, CharSet = CharSet.Unicode)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool BluetoothFindNextDevice(IntPtr hFind, ref BLUETOOTH_DEVICE_INFO pbtdi);

    [DllImport("bthprops.cpl", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool BluetoothFindDeviceClose(IntPtr hFind);
}
