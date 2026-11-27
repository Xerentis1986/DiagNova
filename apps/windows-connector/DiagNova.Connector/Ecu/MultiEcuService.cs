using DiagNova.Connector.Obd;

namespace DiagNova.Connector.Ecu;

/// <summary>
/// Mehr-ECU aus beobachteten OBD-Antworten – kein Blindscan.
/// Lesende Identifikation zuerst.
/// </summary>
public static class MultiEcuService
{
    public static object InventoryFromInitBitmap(IReadOnlyList<ObdEcuFrame> frames, string dataSource, string? protocolName)
    {
        var discovered = new List<object>();
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var frame in frames)
        {
            var norm = ObdEcuAddresses.Normalize(frame.EcuId);
            if (norm is null || !ObdEcuAddresses.IsStandardResponse(norm))
            {
                continue;
            }
            if (!seen.Add(norm))
            {
                continue;
            }

            if (!int.TryParse(norm, System.Globalization.NumberStyles.HexNumber, null, out var respId))
            {
                continue;
            }

            var req = ObdEcuAddresses.RequestForResponse(respId);
            discovered.Add(new
            {
                ecu_id = norm,
                response_hex = norm,
                request_hex = req?.ToString("X3"),
                slot_index = respId - ObdEcuAddresses.PhysicalResponseMin,
                role_hint_de = ObdEcuAddresses.RoleHint(respId),
                verified_source = "ISO 15765-4",
                discovery_method = "observed_response",
                status = "responding",
                identification = (object?)null
            });
        }

        return new
        {
            data_source = dataSource,
            protocol_name = protocolName,
            blind_scan_used = false,
            blind_scan_allowed = false,
            count = discovered.Count,
            discovered_obd_ecus = discovered,
            unavailable_categories = new[]
            {
                new { id = "abs", label_de = "ABS / ESP", reason_de = "Keine verifizierte Adresse – nicht gescannt." },
                new { id = "airbag", label_de = "Airbag / SRS", reason_de = "Keine verifizierte Adresse – nicht gescannt." },
                new { id = "comfort", label_de = "Komfort", reason_de = "Keine verifizierte Adresse – nicht gescannt." },
            },
            message_de = $"{discovered.Count} OBD-Steuergerät(e) aus beobachteten Antworten. Kein Netzwerk-Blindscan.",
            read_policy_de = "Lesende Identifikation, DTCs und Messwerte zuerst."
        };
    }

    public static object CategoriesOverview() => new
    {
        blind_scan_allowed = false,
        categories = new object[]
        {
            new { id = "engine", label_de = "Motor / ECM", availability = "discoverable_obd", source = "ISO 15765-4 0x7E8" },
            new { id = "transmission", label_de = "Getriebe / TCM", availability = "discoverable_obd", source = "ISO 15765-4 0x7E9" },
            new { id = "abs", label_de = "ABS / ESP", availability = "unavailable_no_definition", blocker = "BLK-OEM" },
            new { id = "airbag", label_de = "Airbag / SRS", availability = "unavailable_no_definition", blocker = "BLK-OEM" },
            new { id = "comfort", label_de = "Komfort", availability = "unavailable_no_definition", blocker = "BLK-OEM" },
        }
    };
}
