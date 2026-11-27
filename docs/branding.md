# DiagNova Branding

Kurzreferenz zur integrierten Marke (Charcoal / Teal / White).

## Quelle

Bestätigtes Logo-Paket (Raster/PNG, SVG mit eingebettetem Raster). Keine echten Vektorpfade.

Farben (Annäherung, kein verbindliches CD-Handbuch):

| Token | Hex | CSS |
|-------|-----|-----|
| Charcoal | `#1F2D36` | `--diagnova-charcoal` |
| Teal | `#00A99B` | `--diagnova-teal` |
| White | `#FFFFFF` | `--diagnova-white` |

Tokens leben in `apps/web/src/index.css` und als Kopie unter `apps/web/public/brand/brand-tokens.css`.

## Web

| Asset | Pfad |
|-------|------|
| Favicon | `apps/web/public/favicon.ico` (+ PNG 16/32/48) |
| Apple Touch | `apps/web/public/apple-touch-icon.png` |
| PWA Icons | `apps/web/public/icons/pwa-{192,512}.png` |
| Manifest | `apps/web/public/manifest.webmanifest` |
| Wordmark light | `apps/web/public/brand/wordmark-light.png` |
| Wordmark dark | `apps/web/public/brand/wordmark-dark.png` (Monochrom weiß) |
| Symbol | `apps/web/public/brand/symbol-{64,128,256}.png` |

Einbindung: `BrandMark` (`apps/web/src/components/BrandMark.tsx`) – Theme-aware (hell: charcoal Wordmark, dunkel: weißes Monochrom). Login zeigt Wordmark hero-level; Header/Nav nutzt Symbol + Wordmark-Lockup.

## Windows-Connector

| Asset | Pfad |
|-------|------|
| ApplicationIcon | `apps/windows-connector/DiagNova.Connector/Assets/DiagNova_app.ico` |
| PNG 256 | `…/Assets/DiagNova_windows_256.png` |

Im csproj als `ApplicationIcon` gesetzt.

## Hinweise

- Auf dunklem UI kein charcoal Wordmark (Kontrast) – immer `wordmark-dark` / weißes Monochrom.
- Markenlogos von Fahrzeugherstellern bleiben Text-Fallback (Rechte ungeklärt) – davon unabhängig.
- Live-Deploy (World4You/Plesk) optional; dieses Paket ändert keinen Deploy-Flow.
