import { useState, type KeyboardEvent } from 'react'
import type { Brand } from '../lib/api'
import { useTheme } from '../lib/theme'

interface Props {
  brand: Brand
  favorite: boolean
  onSelect: () => void
  onToggleFavorite: () => void
  tabIndex?: number
  active?: boolean
  tileRef?: (el: HTMLButtonElement | null) => void
  onKeyNavigate?: (e: KeyboardEvent<HTMLButtonElement>) => void
}

export function BrandTile({
  brand,
  favorite,
  onSelect,
  onToggleFavorite,
  tabIndex = 0,
  active = false,
  tileRef,
  onKeyNavigate,
}: Props) {
  const { resolved } = useTheme()
  const [imgFailed, setImgFailed] = useState(false)

  // Original-Emblem (logos/) für volle, unverzerrte Darstellung;
  // vorbereitete Kacheln als Fallback; Initialen zuletzt.
  const tileSrc =
    resolved === 'dark'
      ? brand.logo_tile_dark || brand.logo_tile_light
      : brand.logo_tile_light || brand.logo_tile_dark
  const src = brand.logo_url || tileSrc || null
  const showImage = brand.logo_mode === 'image' && !!src && !imgFailed

  return (
    <div className={`dn-brand-tile group relative ${active ? 'dn-brand-tile--active' : ''}`.trim()}>
      <button
        ref={tileRef}
        type="button"
        tabIndex={tabIndex}
        onClick={onSelect}
        onKeyDown={onKeyNavigate}
        className="flex min-h-[8.5rem] w-full touch-manipulation flex-col items-center gap-3 p-4 text-center focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--dn-accent)]"
        aria-label={`Marke ${brand.name} wählen`}
      >
        <span className="dn-brand-logo" aria-hidden>
          {showImage ? (
            <img
              src={src!}
              alt=""
              width={160}
              height={120}
              loading="lazy"
              decoding="async"
              className="dn-brand-logo__img"
              onError={() => setImgFailed(true)}
            />
          ) : (
            <span className="dn-brand-logo__initials">{brand.logo_initials}</span>
          )}
        </span>
        <span className="text-base font-semibold text-[var(--dn-text)]">{brand.name}</span>
        <span className="text-xs text-[var(--dn-muted)]">{brand.group}</span>
      </button>
      <button
        type="button"
        className="absolute right-2 top-2 flex h-10 w-10 touch-manipulation items-center justify-center rounded-md text-base text-[var(--dn-muted)] hover:bg-[var(--dn-hover)] hover:text-[var(--dn-text)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--dn-accent)]"
        aria-pressed={favorite}
        aria-label={favorite ? `${brand.name} aus Favoriten entfernen` : `${brand.name} zu Favoriten`}
        onClick={(e) => {
          e.stopPropagation()
          onToggleFavorite()
        }}
      >
        {favorite ? '★' : '☆'}
      </button>
    </div>
  )
}
