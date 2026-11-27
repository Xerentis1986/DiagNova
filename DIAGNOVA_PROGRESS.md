# DiagNova – Fortschritt

Zuletzt aktualisiert: **2026-11-27, 18:57 Europe/Vienna**

## Aktueller Stand

| Item | Wert |
|------|------|
| Aktive Phase | **00** Bestandsaufnahme – Doku abgeschlossen |
| Nächste Phase | **02** (nur nach User-Freigabe) |
| MVP-Basis | Branch `cursor/diagnova-phase-ab-mvp-bf17` / PR #1 – **nicht überschreiben** |
| Phase-00-Branch | `cursor/diagnova-phase-00-6d5b` |

## Erledigt

### Phase 01 / A+B MVP (Bestand, nicht Teil dieser Lieferung)
- Monorepo Web + API + Connector-Stub + Docker Compose + Tests
- Simulierte OBD-Diagnose, Demo-Login, Berichte CSV/PDF
- PR: https://github.com/Xerentis1986/DiagNova/pull/1

### Phase 00 (diese Lieferung)
- Inventar Code, DB, API, UI, Connector, Docker, Tests
- Anforderungsmatrix `docs/requirements.md` (IDs, Status, Phase 02–19)
- Capabilities `docs/capabilities.md`
- Phasenstatus `docs/phase-status.md`
- Abschlussbericht `docs/phase-00-abschluss.md`
- Tests tatsächlich ausgeführt (siehe Abschlussbericht)

## Test-Baseline (Phase 00)

```
pytest tests -q
→ 12 passed, 13 warnings

cd apps/web && npm ci && npm run build
→ Erfolg
```

Nicht ausgeführt (Tools fehlen in Cloud-VM): `docker compose`, `dotnet build`, Hardware.

## Blocker (übergreifend)

1. Keine OBD-/Adapter-Hardware; Delphi/Autocom-Modell unbekannt
2. Keine OEM-/ODX-Lizenzen und keine freigegebenen Diagnosedatenquellen
3. Kein Mandantenmodell
4. Docker/.NET in Inventar-Umgebung nicht verfügbar (Compose/Connector-Build nicht hier verifiziert)
5. Keine Live-Fahrzeugkommunikation – alles Simulator

## Nächste Schritte (nur nach Freigabe)

1. Review/Merge Phase-00-PR
2. Explizite Freigabe für **Phase 02** (Marken-Kacheln & Fahrzeugauswahl)
3. Phase 01/MVP unverändert lassen
