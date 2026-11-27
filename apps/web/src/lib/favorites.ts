const FAV_KEY = 'dn_favorite_brands'
const RECENT_LOCAL_KEY = 'dn_recent_local'

export function readLocalFavorites(): string[] {
  try {
    const raw = localStorage.getItem(FAV_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : []
  } catch {
    return []
  }
}

export function writeLocalFavorites(slugs: string[]) {
  localStorage.setItem(FAV_KEY, JSON.stringify(slugs))
}

export function toggleLocalFavorite(slug: string): string[] {
  const current = readLocalFavorites()
  const next = current.includes(slug) ? current.filter((s) => s !== slug) : [...current, slug]
  writeLocalFavorites(next)
  return next
}

export interface LocalRecent {
  brand_slug: string
  brand_name: string
  model_name: string
  series?: string | null
  year?: number | null
  engine?: string | null
  vin?: string | null
  vehicle_id?: string | null
  used_at: string
}

export function readLocalRecent(): LocalRecent[] {
  try {
    const raw = localStorage.getItem(RECENT_LOCAL_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? (parsed as LocalRecent[]) : []
  } catch {
    return []
  }
}

export function pushLocalRecent(entry: Omit<LocalRecent, 'used_at'>) {
  const next: LocalRecent[] = [
    { ...entry, used_at: new Date().toISOString() },
    ...readLocalRecent().filter(
      (r) => !(r.brand_slug === entry.brand_slug && r.model_name === entry.model_name && r.vin === entry.vin),
    ),
  ].slice(0, 12)
  localStorage.setItem(RECENT_LOCAL_KEY, JSON.stringify(next))
  return next
}
