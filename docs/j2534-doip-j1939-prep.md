# Vorbereitung: J2534, DoIP, J1939/RP1210 (Phase 05 / 12 / 19)

**Status:** nur Dokumentation / Schnittstellen-Vorbereitung – **keine** laufende Diagnose-Implementierung.  
**Kein** Hardwaretest, **keine** Freigabe.  
**Phase 12:** API `/api/coding/interfaces` und Katalogeinträge `J2534_PASSTHRU_PREP` / `DPDU_MVCI_PREP` spiegeln diesen Prep-Status; Flash bleibt 403.  
**Phase 19:** LKW-Architektur, Capability-Flags, UI „Geplant“ – Details in [lkw-j1939-architecture.md](./lkw-j1939-architecture.md).

## SAE J2534 PassThru

- Rolle: Windows-DLL-API für PassThru-Boxen (ISO-TP/UDS/OBD je nach Gerät).
- DiagNova: Adapter-Eintrag `j2534-passthru` in Capability-Matrix mit Status `planned`.
- Blocker: BLK-HW (kein Gerät), keine Vendor-DLL im Repo.
- Nächster Schritt bei Hardware: DLL laden, `PassThruOpen`/`Connect`/`ReadMsgs` hinter Transport-Schicht – nicht in dieser Phase.

## ISO 13400 DoIP

- Rolle: Diagnose über IP (Ethernet), typisch moderne Fahrzeuge.
- DiagNova: Protokollkatalog `iso_13400_doip` = `documented_prep`; Adapter `doip-ethernet` geplant.
- **ELM327/OBD-Dongle ersetzt DoIP nicht.**
- Blocker: BLK-HW, Netzwerkstack + Vehicle Discovery.

## ISO 22900 D-PDU / MVCI

- Hardware-API-Familie; oft proprietäre Runtimes.
- Status: `documented_prep` – keine Runtime/Lizenz im Repo.

## SAE J1939 / RP1210 (Phase 19)

- LKW/Nutzfahrzeuge, oft 24 V, RP1210-Adapter.
- Katalog-Status: `documented_prep` (Architektur Phase 19).
- Adapter-Eintrag `rp1210-commercial` in Capability-Matrix: `planned`, `hardware_tested=false`.
- API: `/api/lkw/*` – Diagnose-POSTs → 403.
- **Kein** J1939-Parser, **kein** Fake-LKW-Simulator.
- J1708/J1587: ebenfalls `documented_prep`.

## Abgrenzung zur aktuellen Codebasis

| Vorhanden | Nicht vorhanden |
|-----------|-----------------|
| OBD über ELM/Fake Allowlist | J2534 DLL-Bindung |
| ISO-TP Framing-Parser (Testvektoren) | DoIP Routing Activation |
| UDS NRC-Tabelle | SecurityAccess / Flash |
| ISO 15765-4 Adressen 7E0–7EF | OEM-Netzwerkscan |
