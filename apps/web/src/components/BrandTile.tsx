import type { KeyboardEvent } from 'react'
import type { Brand } from '../lib/api'

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
  return (
    <div className={`dn-brand-tile group relative ${active ? 'dn-brand-tile--active' : ''}`.trim()}>
      <button
        ref={tileRef}
        type="button"
        tabIndex={tabIndex}
        onClick={onSelect}
        onKeyDown={onKeyNavigate}
        className="flex min-h-[7.5rem] w-full touch-manipulation flex-col items-center gap-3 p-4 text-center focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--dn-accent)]"
        aria-label={`Marke ${brand.name} wählen`}
      >
        <span
          className="dn-brand-logo flex h-16 w-16 items-center justify-center text-lg font-semibold tracking-wide"
          aria-hidden
          title="Text-Fallback – Markenlogo-Rechte nicht freigegeben"
        >
          {brand.logo_initials}
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
