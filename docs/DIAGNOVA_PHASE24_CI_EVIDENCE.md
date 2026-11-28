# Phase 24 – CI Evidence

## Phase 23 Tip (Basis)
- Run `46088694592` / `46088682770`: **success**, 8 Checks
- Installer-Artefakt erfolgreich hochgeladen

## Phase 24
- Workflow: `.github/workflows/ci.yml` (+ SHA256-Schritt für Installer)
- Nach Push dieses Branches: CI erneut – Ergebnis in PR Checks
- Lokal vor Push: pytest 156, dotnet 55, web build PASS
