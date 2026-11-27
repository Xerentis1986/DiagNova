import type { Brand } from '../lib/api'

interface Props {
  brand: Brand
  favorite: boolean
  onSelect: () => void
  onToggleFavorite: () => void
}

export function BrandTile({ brand, favorite, onSelect, onToggleFavorite }: Props) {
  return (
    <div className="dn-brand-tile group relative">
      <button
        type="button"
        onClick={onSelect}
        className="flex w-full flex-col items-center gap-3 p-4 text-center focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--dn-accent)]"
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
        className="absolute right-2 top-2 rounded-md px-2 py-1 text-sm text-[var(--dn-muted)] hover:bg-[var(--dn-hover)] hover:text-[var(--dn-text)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--dn-accent)]"
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
