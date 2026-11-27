import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BrandTile } from '../components/BrandTile'
import { api } from '../lib/api'
import { readLocalFavorites, writeLocalFavorites } from '../lib/favorites'

export function BrandsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [query, setQuery] = useState('')
  const [localFavs, setLocalFavs] = useState<string[]>(() => readLocalFavorites())

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
      <header className="space-y-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-[var(--dn-text)]">Markenübersicht</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--dn-muted)]">
              DACH-Katalog zur Fahrzeugauswahl. Katalogeintrag bedeutet keine Diagnoseabdeckung.
              Markenlogos nur als Text-Fallback (Rechte ungeklärt).
            </p>
          </div>
          <Link
            to="/vehicles"
            className="rounded-md border border-[var(--dn-border)] px-3 py-2 text-sm hover:bg-[var(--dn-hover)]"
          >
            Fahrzeugliste
          </Link>
        </div>
        <label className="block max-w-xl">
          <span className="sr-only">Marke suchen</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Marke suchen…"
            className="dn-input w-full"
            autoComplete="off"
          />
        </label>
      </header>

      {recentQuery.data && recentQuery.data.length > 0 && (
        <section aria-labelledby="recent-heading" className="space-y-3">
          <h2 id="recent-heading" className="text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
            Zuletzt verwendet
          </h2>
          <ul className="flex flex-wrap gap-2">
            {recentQuery.data.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  className="rounded-md border border-[var(--dn-border)] bg-[var(--dn-panel)] px-3 py-2 text-left text-sm hover:bg-[var(--dn-hover)]"
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

      {favoriteBrands.length > 0 && !query.trim() && (
        <section aria-labelledby="fav-heading" className="space-y-3">
          <h2 id="fav-heading" className="text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
            Favoriten
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
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

      <section aria-labelledby="all-brands-heading" className="space-y-3">
        <h2 id="all-brands-heading" className="text-sm font-medium uppercase tracking-wide text-[var(--dn-muted)]">
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
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {brands.map((b) => (
            <BrandTile
              key={b.slug}
              brand={b}
              favorite={favoriteSlugs.includes(b.slug)}
              onSelect={() => navigate(`/select/${b.slug}`)}
              onToggleFavorite={() => toggleFavorite(b.slug)}
            />
          ))}
        </div>
      </section>
    </div>
  )
}
