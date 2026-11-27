import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrandTile } from '../components/BrandTile'
import { IconClock, IconDiagnose, IconEngine, IconSearch, IconStar } from '../components/icons'
import { Input } from '../components/ui'
import { api } from '../lib/api'
import { readLocalFavorites, writeLocalFavorites } from '../lib/favorites'

export function BrandsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [query, setQuery] = useState('')
  const [localFavs, setLocalFavs] = useState<string[]>(() => readLocalFavorites())
  const [focusIndex, setFocusIndex] = useState(0)
  const [showFavs, setShowFavs] = useState(false)
  const tileRefs = useRef<Array<HTMLButtonElement | null>>([])

  const brandsQuery = useQuery({
    queryKey: ['catalog-brands', query],
    queryFn: () => api.catalogBrands(query.trim() || undefined),
  })

  const favoritesQuery = useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      const remote = await api.getFavorites()
      if (remote.brand_slugs.length) {
        writeLocalFavorites(remote.brand_slugs)
        setLocalFavs(remote.brand_slugs)
        return remote.brand_slugs
      }
      return readLocalFavorites()
    },
  })

  const recentQuery = useQuery({
    queryKey: ['recent-selections'],
    queryFn: () => api.recentSelections(),
  })

  const favMutation = useMutation({
    mutationFn: (slugs: string[]) => api.putFavorites(slugs),
    onSuccess: (data) => {
      writeLocalFavorites(data.brand_slugs)
      setLocalFavs(data.brand_slugs)
      void qc.invalidateQueries({ queryKey: ['favorites'] })
    },
  })

  const favoriteSlugs = favoritesQuery.data ?? localFavs
  const brands = brandsQuery.data ?? []
  const favoriteBrands = useMemo(
    () => brands.filter((b) => favoriteSlugs.includes(b.slug)),
    [brands, favoriteSlugs],
  )

  useEffect(() => {
    setFocusIndex(0)
    tileRefs.current = []
  }, [brands])

  const cols = useMemo(() => {
    if (typeof window === 'undefined') return 2
    const w = window.innerWidth
    if (w >= 1280) return 7
    if (w >= 1024) return 6
    if (w >= 768) return 4
    if (w >= 640) return 3
    return 2
  }, [brands.length])

  const moveFocus = useCallback(
    (next: number) => {
      if (!brands.length) return
      const clamped = ((next % brands.length) + brands.length) % brands.length
      setFocusIndex(clamped)
      tileRefs.current[clamped]?.focus()
    },
    [brands.length],
  )

  function onTileKey(e: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      moveFocus(index + 1)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      moveFocus(index - 1)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      moveFocus(index + cols)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      moveFocus(index - cols)
    } else if (e.key === 'Home') {
      e.preventDefault()
      moveFocus(0)
    } else if (e.key === 'End') {
      e.preventDefault()
      moveFocus(brands.length - 1)
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      navigate(`/select/${brands[index].slug}`)
    }
  }

  function toggleFavorite(slug: string) {
    const next = favoriteSlugs.includes(slug)
      ? favoriteSlugs.filter((s) => s !== slug)
      : [...favoriteSlugs, slug]
    writeLocalFavorites(next)
    setLocalFavs(next)
    favMutation.mutate(next)
  }

  return (
    <div className="space-y-8">
      <header className="dn-brands-hero">
        <h1 className="dn-page-title text-[1.75rem] sm:text-[2rem]">Fahrzeugmarke auswählen</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm text-[var(--dn-muted)]">
          Wählen Sie eine Automarke, um die Diagnose zu starten. Katalogeintrag bedeutet keine
          Diagnoseabdeckung.
        </p>
        {/* Visuell versteckte Überschrift für bestehende E2E-/A11y-Referenzen */}
        <p className="sr-only">Markenübersicht</p>
        <label className="dn-brands-search block">
          <span className="sr-only">Marke suchen</span>
          <span className="dn-brands-search__icon">
            <IconSearch />
          </span>
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Marke suchen…"
            autoComplete="off"
            enterKeyHint="search"
          />
        </label>
      </header>

      {recentQuery.data && recentQuery.data.length > 0 && (
        <section aria-labelledby="recent-heading" className="space-y-3">
          <h2 id="recent-heading" className="dn-section-title">
            Zuletzt verwendet
          </h2>
          <ul className="flex flex-wrap gap-2">
            {recentQuery.data.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  className="dn-btn dn-btn--secondary touch-manipulation text-left"
                  onClick={() => {
                    if (r.vehicle_id) {
                      localStorage.setItem('dn_active_vehicle', r.vehicle_id)
                      navigate(`/select/${r.brand_slug}?resume=${r.vehicle_id}`)
                    } else {
                      navigate(`/select/${r.brand_slug}`)
                    }
                  }}
                >
                  <span className="font-medium">
                    {r.brand_name} {r.model_name}
                  </span>
                  <span className="ml-2 text-[var(--dn-muted)]">
                    {r.year ?? ''} {r.engine ?? ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {(showFavs || (!query.trim() && favoriteBrands.length > 0)) && favoriteBrands.length > 0 && (
        <section aria-labelledby="fav-heading" className="space-y-3">
          <h2 id="fav-heading" className="dn-section-title">
            Favoriten
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-7">
            {favoriteBrands.map((b) => (
              <BrandTile
                key={`fav-${b.slug}`}
                brand={b}
                favorite
                onSelect={() => navigate(`/select/${b.slug}`)}
                onToggleFavorite={() => toggleFavorite(b.slug)}
              />
            ))}
          </div>
        </section>
      )}

      <section aria-labelledby="all-brands-heading" className="space-y-4">
        <h2 id="all-brands-heading" className="dn-section-title">
          Alle Marken
        </h2>
        {brandsQuery.isLoading && <p className="text-[var(--dn-muted)]">Marken werden geladen…</p>}
        {brandsQuery.error && (
          <p className="text-[var(--dn-danger)]">Markenkatalog konnte nicht geladen werden.</p>
        )}
        {!brandsQuery.isLoading && brands.length === 0 && (
          <div className="dn-panel p-8 text-center" role="status">
            <p className="text-lg font-medium">Keine Marken gefunden</p>
            <p className="mt-1 text-sm text-[var(--dn-muted)]">
              Suche anpassen oder Filter leeren. Weitere Marken später per Datenimport (Phase 06).
            </p>
          </div>
        )}
        <div
          className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-7"
          role="listbox"
          aria-label="Markenkatalog"
        >
          {brands.map((b, index) => (
            <div key={b.slug} role="option" aria-selected={focusIndex === index}>
              <BrandTile
                brand={b}
                favorite={favoriteSlugs.includes(b.slug)}
                active={focusIndex === index}
                tabIndex={focusIndex === index ? 0 : -1}
                tileRef={(el) => {
                  tileRefs.current[index] = el
                }}
                onSelect={() => navigate(`/select/${b.slug}`)}
                onToggleFavorite={() => toggleFavorite(b.slug)}
                onKeyNavigate={(e) => onTileKey(e, index)}
              />
            </div>
          ))}
        </div>
      </section>

      <section aria-label="Schnellaktionen" className="dn-action-grid pt-2">
        <button type="button" className="dn-action-card" onClick={() => navigate('/diagnostics')}>
          <span className="dn-action-card__icon">
            <IconEngine />
          </span>
          <span>
            <span className="dn-action-card__title">OBD generische Diagnose</span>
            <span className="dn-action-card__sub block">Standard-OBD ohne Markenwahl</span>
          </span>
        </button>
        <button type="button" className="dn-action-card" onClick={() => navigate('/ecu')}>
          <span className="dn-action-card__icon">
            <IconDiagnose />
          </span>
          <span>
            <span className="dn-action-card__title">Schnellscan (alle Steuergeräte)</span>
            <span className="dn-action-card__sub block">Simulierter Mehr-ECU-Überblick</span>
          </span>
        </button>
        <button
          type="button"
          className="dn-action-card"
          onClick={() => {
            setShowFavs(false)
            document.getElementById('recent-heading')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}
        >
          <span className="dn-action-card__icon">
            <IconClock />
          </span>
          <span>
            <span className="dn-action-card__title">Letzte Fahrzeuge</span>
            <span className="dn-action-card__sub block">
              {recentQuery.data?.length ? `${recentQuery.data.length} Einträge` : 'Noch keine'}
            </span>
          </span>
        </button>
        <button
          type="button"
          className="dn-action-card"
          onClick={() => {
            setShowFavs(true)
            document.getElementById('fav-heading')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }}
        >
          <span className="dn-action-card__icon">
            <IconStar />
          </span>
          <span>
            <span className="dn-action-card__title">Favoriten</span>
            <span className="dn-action-card__sub block">
              {favoriteSlugs.length ? `${favoriteSlugs.length} Marken` : 'Keine gesetzt'}
            </span>
          </span>
        </button>
      </section>
    </div>
  )
}
