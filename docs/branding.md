# DiagNova Branding

Kurzreferenz zur integrierten Marke und zum Designsystem (Phase 10B).

## Quelle

Bestätigtes Logo-Paket (Raster/PNG, SVG mit eingebettetem Raster). Keine echten Vektorpfade.
Keine neuen Logoentwürfe – Diag anthrazit, Nova türkis, OBD2-Stecker im D.

## Farben (verbindlich Phase 10B)

| Token | Hex | CSS |
|-------|-----|-----|
| Charcoal | `#1F2D36` | `--diagnova-charcoal` |
| Teal | `#00B3A3` | `--diagnova-teal` (Paket-Altwert `#00A99B` als `--diagnova-teal-legacy`) |
| Hell | `#F8FAFB` | `--diagnova-light` |
| Dunkel | `#111A20` | `--diagnova-dark` |
| White | `#FFFFFF` | `--diagnova-white` |

Tokens: `apps/web/src/index.css`, Kopie `apps/web/public/brand/brand-tokens.css`.

## Designsystem

React/Tailwind-Primitives unter `apps/web/src/components/ui/`:

- `Button`, `Field`/`Input`/`Select`, `Table`, `Dialog`, `Panel`/`PageHeader`/`Badge`
- Shell: `AppShell` (Sidebar + Topbar) – UX-Ziel Mockup Fahrzeugauswahl, Brand-Teal statt Royalblau
- Theme: Hell / Dunkel / System (`ThemeToggle`, `lib/theme.tsx`)

## Web

| Asset | Pfad |
|-------|------|
| Favicon | `apps/web/public/favicon.ico` (+ PNG 16–180) |
| Apple Touch | `apps/web/public/apple-touch-icon.png` |
| PWA Icons | `apps/web/public/icons/pwa-{192,512}.png` |
| Manifest | `apps/web/public/manifest.webmanifest` |
| Wordmark light/dark | `apps/web/public/brand/wordmark-*.png` |
| Symbol | `apps/web/public/brand/symbol-{64,128,256}.png` |

`BrandMark`: Theme-aware (hell: charcoal Wordmark, dunkel: weißes Monochrom). Login Wordmark hero-level; Sidebar Lockup.

## PDF / Connector

| Asset | Pfad |
|-------|------|
| PDF-Fallback Symbol | `apps/api/app/assets/diagnova_symbol_128.png` |
| PDF-Fallback Wordmark | `apps/api/app/assets/diagnova_wordmark_800.png` |
| Windows ApplicationIcon | `apps/windows-connector/.../Assets/DiagNova_app.ico` |

PDF-Kopf: Werkstattlogo wenn vorhanden, sonst DiagNova-Symbol.

## Hinweise

- Dunkles UI: immer `wordmark-dark` / weißes Monochrom (Kontrast).
- Herstellerlogos: PNG unter `apps/web/public/brand-logos/` (Dataset-Attribution dort);
  Katalog liefert `logo_mode=image` / `logo_url` nach Produktfreigabe.
- Mockup unter Store `media/brand/ui-mockup-fahrzeugauswahl.png` ist UX-Ziel, kein Pixel-Clone.
