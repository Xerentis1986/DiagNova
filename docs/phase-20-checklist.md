# Phase 20 – Checkliste Systemprüfung

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-20-readiness-e3f2`

## Integration

- [x] Neuesten integrierbaren Stand gewählt (nicht leeres `main`)
- [x] Phase 18 + 19 auf Phase-17-Tip gemerged
- [x] Konflikte gelöst (Router, API-Typen, Dashboard, Docs)
- [x] Doppelter `lkw`-Dashboard-Eintrag entfernt

## Audit-Trennung

- [x] Implementiert vs. automatisiert getestet dokumentiert
- [x] Simuliert vs. nicht verifiziert (HW/Lizenz) getrennt
- [x] Flash/Service/Tuning-Schreiben als gesperrt bestätigt
- [x] Markenlogos: Text-Fallback / BLK-LOGO
- [x] Deploy/Live: Smoke only, BLK-DEPLOY

## Fixes (ohne Flash / ohne Prod ohne Freigabe)

- [x] `using Xunit` in `Phase14UpdateTests.cs`
- [x] Connector csproj-Version → 0.15.0
- [x] Connector-README Publish-Hinweis
- [x] `.gitignore` publish/exe
- [x] Phase-20-Integrations-Tests

## Windows-Connector

- [x] Build-Pfad dokumentiert (`dotnet build/run/test`)
- [x] Fehlende EXE ehrlich dokumentiert
- [x] BT/COM/Adapter-Status ehrlich (Inventar ja, SPP/HW nein)
- [x] `dotnet test` ausgeführt (32 passed)

## Tests

- [x] pytest – 148 passed
- [x] Web build – OK
- [x] dotnet test – 32 passed
- [ ] Docker Compose in Agent-VM – nicht möglich (BLK-DOCKER)

## Live (read-only)

- [x] `GET /` → 200
- [x] `GET /health` → 200, simulated/demo
- [x] Favicon/Manifest → 200
- [x] Kein Redeploy

## Berichte / Progress

- [x] `docs/phase-20-abschluss.md`
- [x] `docs/phase-20-commercial-readiness.md` (GO/NO-GO)
- [x] `docs/phase-20-checklist.md`
- [x] `DIAGNOVA_PROGRESS.md` aktualisiert
- [x] Store-Kopien unter Project-Store `docs/`

## Freigaben (offen – nicht erteilt)

- [ ] Flash-/Service-Schreibfreigabe – **verweigert laut Auftrag**
- [ ] Prod-Redeploy – **STOP**
- [ ] Hardware-/OEM-/Legal-/PAY-Freigaben – offen
