namespace DiagNova.Connector.Obd;

/// <summary>Dokumentierte SAE-J1979-Skalierungen für gängige Mode-01-PIDs.</summary>
public static class ObdPidScaler
{
    public static readonly IReadOnlyDictionary<int, PidMeta> Definitions = new Dictionary<int, PidMeta>
    {
        [0x04] = new(0x04, "engine_load", "%", "Berechnete Motorlast", 1),
        [0x05] = new(0x05, "coolant_temp", "°C", "Kühlmitteltemperatur", 1),
        [0x0C] = new(0x0C, "rpm", "1/min", "Motordrehzahl", 2),
        [0x0D] = new(0x0D, "speed", "km/h", "Fahrzeuggeschwindigkeit", 1),
        [0x0F] = new(0x0F, "intake_temp", "°C", "Ansauglufttemperatur", 1),
        [0x10] = new(0x10, "maf", "g/s", "Luftmassenstrom", 2),
        [0x11] = new(0x11, "throttle", "%", "Drosselklappenstellung", 1),
        [0x2F] = new(0x2F, "fuel_level", "%", "Kraftstofffüllstand", 1),
        [0x42] = new(0x42, "control_module_voltage", "V", "Steuergerätespannung", 2),
    };

    public static ObdPidReading Scale(int pid, IReadOnlyList<byte> data, string? ecuId)
    {
        var ts = DateTimeOffset.UtcNow;
        if (!Definitions.TryGetValue(pid, out var meta))
        {
            return new ObdPidReading(pid, $"pid_0x{pid:X2}", $"Unbekannte PID 0x{pid:X2}", null, "",
                "unknown_pid", ecuId ?? "unknown", ts);
        }
        if (data.Count < meta.BytesNeeded)
        {
            return new ObdPidReading(pid, meta.Name, meta.DescriptionDe, null, meta.Unit,
                "truncated", ecuId ?? "unknown", ts);
        }

        double value = meta.Pid switch
        {
            0x04 or 0x11 or 0x2F => data[0] * 100.0 / 255.0,
            0x05 or 0x0F => data[0] - 40,
            0x0C => ((data[0] * 256) + data[1]) / 4.0,
            0x0D => data[0],
            0x10 => ((data[0] * 256) + data[1]) / 100.0,
            0x42 => ((data[0] * 256) + data[1]) / 1000.0,
            _ => double.NaN
        };

        if (double.IsNaN(value))
        {
            return new ObdPidReading(pid, meta.Name, meta.DescriptionDe, null, meta.Unit,
                "unknown_scale", ecuId ?? "unknown", ts);
        }

        return new ObdPidReading(pid, meta.Name, meta.DescriptionDe, Math.Round(value, 3), meta.Unit,
            "ok", ecuId ?? "unknown", ts);
    }

    public sealed record PidMeta(int Pid, string Name, string Unit, string DescriptionDe, int BytesNeeded);
}
