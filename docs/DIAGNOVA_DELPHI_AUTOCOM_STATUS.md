# Delphi / Autocom – Status (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Kompatibilitätsstatus:** `ManufacturerApprovalRequired`  
**hardware_tested:** false · **vehicle_tested:** false

## Recherche

1. **Gerät:** Offiziell beworben u. a. **DS150E** (VCI) / **DS450E** (Tablet). Exakte Serien-/Firmware der vorhandenen Einheit: **nicht** in dieser Umgebung ermittelt.
2. **Original vs. Clone:** unbekannt – muss vor Integration geklärt werden.
3. **USB / Bluetooth:** Delphi dokumentiert USB und Bluetooth (SPP) für die **eigene** Diagnosesoftware.
4. **VID/PID / Treiber / Firmware:** ausstehend (lokale Inventur).
5. **Offizielle Drittanbieter-API / SDK:** **nicht** öffentlich nachgewiesen.
6. **J2534:** nicht belegt für dieses Gerät – J2534-Abstraktion ≠ Delphi-Support.
7. **Rechtliches:** Keine proprietären Bibliotheken ohne Nutzungsrechte; kein Umgehen von Lizenzschutz.

## Implementierung

- Profil `delphi-autocom` im Connector-Katalog
- Auswahl/Verbindungstest **verweigert** ohne Freigabe
- Hersteller-Anfrageentwurf unter `/hardware/manufacturer-inquiry-draft`
- Bestehendes Doc `docs/delphi-autocom-interface.md` bleibt gültig (blocked)

## Alternative

Modulare **J2534 PassThru**-Abstraktion für **andere**, nachweislich J2534-fähige Adapter (`/j2534/status`) – explizit getrennt von Delphi.

## Offen

- Geräteidentifikation vor Ort
- Offizielle Entwicklerressourcen / Vertrag
- Erst dann rechtmäßige Treiberanbindung
