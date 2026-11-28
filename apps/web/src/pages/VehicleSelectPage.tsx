import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { pushLocalRecent } from '../lib/favorites'

type Step = 'model' | 'variant' | 'confirm' | 'done'

export function VehicleSelectPage() {
  const { brandSlug = '' } = useParams()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('model')
  const [modelId, setModelId] = useState<string | null>(null)
  const [variantId, setVariantId] = useState<string | null>(null)
  const [year, setYear] = useState<number | null>(null)
  const [vin, setVin] = useState('')
  const [plate, setPlate] = useState('')
  const [odometer, setOdometer] = useState('')
  const [error, setError] = useState<string | null>(null)

  const brandQuery = useQuery({
    queryKey: ['brand', brandSlug],
    queryFn: async () => {
      const brands = await api.catalogBrands()
      const brand = brands.find((b) => b.slug === brandSlug)
      if (!brand) throw new Error('Marke nicht gefunden')
      return brand
    },
    enabled: !!brandSlug,
  })

  const modelsQuery = useQuery({
    queryKey: ['models', brandSlug],
    queryFn: () => api.catalogModels(brandSlug),
    enabled: !!brandSlug,
  })

  const variantsQuery = useQuery({
    queryKey: ['variants', brandSlug, modelId],
    queryFn: () => api.catalogVariants(brandSlug, modelId!),
    enabled: !!brandSlug && !!modelId,
  })

  const capsQuery = useQuery({
    queryKey: ['capabilities', brandSlug],
    queryFn: () => api.catalogCapabilities(brandSlug),
    enabled: !!brandSlug,
  })

  const selectedModel = useMemo(
    () => modelsQuery.data?.find((m) => m.id === modelId) ?? null,
    [modelsQuery.data, modelId],
  )
  const selectedVariant = useMemo(
    () => variantsQuery.data?.find((v) => v.id === variantId) ?? null,
    [variantsQuery.data, variantId],
  )

  const confirmMutation = useMutation({
    mutationFn: () =>
      api.confirmVehicle({
        brand_slug: brandSlug,
        model_id: modelId!,
        variant_id: variantId!,
        year: year!,
        vin: vin.trim().toUpperCase(),
        license_plate: plate.trim() || null,
        odometer_km: odometer.trim() ? Number(odometer) : null,
      }),
    onSuccess: (vehicle) => {
      localStorage.setItem('dn_active_vehicle', vehicle.id)
      pushLocalRecent({
        brand_slug: brandSlug,
        brand_name: vehicle.make,
        model_name: vehicle.model,
        series: vehicle.series,
        year: vehicle.year,
        engine: vehicle.engine,
        vin: vehicle.vin,
        vehicle_id: vehicle.id,
      })
      setStep('done')
      setError(null)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Bestätigung fehlgeschlagen')
    },
  })

  const brand = brandQuery.data

  if (brandQuery.isLoading || modelsQuery.isLoading) {
    return <p className="text-[var(--dn-muted)]">Auswahl wird geladen…</p>
  }
  if (brandQuery.error || !brand) {
    return (
      <div className="dn-panel space-y-3 p-6">
        <p className="text-[var(--dn-danger)]">Marke nicht gefunden.</p>
        <Link to="/" className="text-[var(--dn-accent)] underline">
          Zurück zur Markenübersicht
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <nav className="text-sm text-[var(--dn-muted)]" aria-label="Brotkrumen">
        <Link to="/" className="hover:text-[var(--dn-text)]">
          Marken
        </Link>
        <span aria-hidden> / </span>
        <span className="text-[var(--dn-text)]">{brand.name}</span>
      </nav>

      <header>
        <h1 className="text-2xl font-semibold">{brand.name} – Fahrzeugauswahl</h1>
        <p className="mt-1 text-sm text-[var(--dn-muted)]">{brand.coverage_disclaimer_de}</p>
      </header>

      <ol className="flex flex-wrap gap-2 text-xs" aria-label="Auswahlschritte">
        {[
          { id: 'model', label: '1. Modell' },
          { id: 'variant', label: '2. Baureihe / Motor' },
          { id: 'confirm', label: '3. Bestätigen' },
          { id: 'done', label: '4. Weiter' },
        ].map((s) => (
          <li
            key={s.id}
            className={`rounded-full px-3 py-1 ${
              step === s.id
                ? 'bg-[var(--dn-accent)] text-white'
                : 'border border-[var(--dn-border)] text-[var(--dn-muted)]'
            }`}
          >
            {s.label}
          </li>
        ))}
      </ol>

      {step === 'model' && (
        <section className="dn-panel space-y-3 p-4" aria-labelledby="model-step">
          <h2 id="model-step" className="font-medium">
            Modell wählen
          </h2>
          {(modelsQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-[var(--dn-muted)]">Keine Modelle im Katalog (leerer Zustand).</p>
          ) : (
            <ul className="grid gap-2 sm:grid-cols-2">
              {(modelsQuery.data ?? []).map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    className="w-full rounded-md border border-[var(--dn-border)] px-4 py-3 text-left hover:bg-[var(--dn-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--dn-accent)]"
                    onClick={() => {
                      setModelId(m.id)
                      setVariantId(null)
                      setYear(null)
                      setStep('variant')
                    }}
                  >
                    <span className="font-medium">{m.name}</span>
                    <span className="ml-2 text-xs text-[var(--dn-muted)]">{m.variant_count} Varianten</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {step === 'variant' && selectedModel && (
        <section className="dn-panel space-y-3 p-4" aria-labelledby="variant-step">
          <div className="flex items-center justify-between gap-2">
            <h2 id="variant-step" className="font-medium">
              Baureihe / Baujahr / Motorisierung – {selectedModel.name}
            </h2>
            <button type="button" className="text-sm text-[var(--dn-accent)]" onClick={() => setStep('model')}>
              Zurück
            </button>
          </div>
          {variantsQuery.isLoading && <p className="text-[var(--dn-muted)]">Varianten laden…</p>}
          <ul className="space-y-2">
            {(variantsQuery.data ?? []).map((v) => (
              <li key={v.id}>
                <button
                  type="button"
                  className="w-full rounded-md border border-[var(--dn-border)] px-4 py-3 text-left hover:bg-[var(--dn-hover)]"
                  onClick={() => {
                    setVariantId(v.id)
                    setYear(v.year_from)
                    setStep('confirm')
                  }}
                >
                  <div className="font-medium">
                    Baureihe {v.series} · {v.engine} · {v.fuel_type}
                  </div>
                  <div className="text-xs text-[var(--dn-muted)]">
                    Baujahre {v.year_from}–{v.year_to}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {step === 'confirm' && selectedModel && selectedVariant && (
        <section className="dn-panel space-y-4 p-4" aria-labelledby="confirm-step">
          <div className="flex items-center justify-between gap-2">
            <h2 id="confirm-step" className="font-medium">
              Fahrzeug bestätigen
            </h2>
            <button type="button" className="text-sm text-[var(--dn-accent)]" onClick={() => setStep('variant')}>
              Zurück
            </button>
          </div>
          <p className="text-sm text-[var(--dn-muted)]">
            {brand.name} {selectedModel.name} · {selectedVariant.series} · {selectedVariant.engine}
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="mb-1 block text-[var(--dn-muted)]">Baujahr</span>
              <input
                className="dn-input w-full"
                type="number"
                min={selectedVariant.year_from}
                max={selectedVariant.year_to}
                value={year ?? ''}
                onChange={(e) => setYear(Number(e.target.value))}
                required
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-[var(--dn-muted)]">Kilometerstand</span>
              <input
                className="dn-input w-full"
                type="number"
                min={0}
                value={odometer}
                onChange={(e) => setOdometer(e.target.value)}
                placeholder="optional"
              />
            </label>
            <label className="block text-sm sm:col-span-2">
              <span className="mb-1 block text-[var(--dn-muted)]">VIN (17 Zeichen, manuell korrigierbar)</span>
              <input
                className="dn-input w-full font-mono uppercase"
                value={vin}
                onChange={(e) => setVin(e.target.value.toUpperCase())}
                maxLength={17}
                minLength={17}
                required
                placeholder="z. B. WVWZZZ1JZXW000001"
                autoComplete="off"
              />
            </label>
            <label className="block text-sm sm:col-span-2">
              <span className="mb-1 block text-[var(--dn-muted)]">Kennzeichen</span>
              <input
                className="dn-input w-full"
                value={plate}
                onChange={(e) => setPlate(e.target.value)}
                placeholder="optional"
              />
            </label>
          </div>

          {capsQuery.data && (
            <div className="rounded-md border border-[var(--dn-border)] p-3 text-sm">
              <p className="font-medium">Verfügbare Funktionen</p>
              <p className="mt-1 text-xs text-[var(--dn-warn)]">{capsQuery.data.disclaimer_de}</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {capsQuery.data.available.map((c) => (
                  <li key={c.id}>
                    {c.label_de}{' '}
                    <span className="text-xs uppercase text-[var(--dn-muted)]">({c.status})</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-[var(--dn-muted)]">Nicht verfügbar / geplant:</p>
              <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--dn-muted)]">
                {capsQuery.data.unavailable.map((c) => (
                  <li key={c.id}>{c.label_de}</li>
                ))}
              </ul>
            </div>
          )}

          {error && <p className="text-sm text-[var(--dn-danger)]">{error}</p>}

          <button
            type="button"
            disabled={confirmMutation.isPending || !year || vin.trim().length !== 17}
            className="rounded-md bg-[var(--dn-accent)] px-4 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            onClick={() => confirmMutation.mutate()}
          >
            {confirmMutation.isPending ? 'Speichern…' : 'Fahrzeug bestätigen'}
          </button>
        </section>
      )}

      {step === 'done' && confirmMutation.data && (
        <section className="dn-panel space-y-4 p-4" aria-labelledby="done-step">
          <h2 id="done-step" className="font-medium text-[var(--dn-ok)]">
            Fahrzeug bestätigt
          </h2>
          <p className="text-sm">
            {confirmMutation.data.make} {confirmMutation.data.model} ({confirmMutation.data.year}) · VIN{' '}
            <span className="font-mono">{confirmMutation.data.vin}</span>
          </p>
          <p className="text-sm text-[var(--dn-muted)]">
            Nächster Schritt: Adapter verbinden → Diagnose. Im MVP steht nur der Simulator bereit (Phase 03 für
            echte Adapter).
          </p>
          <div className="flex flex-wrap gap-2">
            <Link
              to={`/diagnostics?vehicle=${confirmMutation.data.id}`}
              className="rounded-md bg-[var(--dn-accent)] px-4 py-2 text-sm text-white"
            >
              Zur Diagnose (Simulator)
            </Link>
            <button
              type="button"
              className="rounded-md border border-[var(--dn-border)] px-4 py-2 text-sm"
              onClick={() => navigate('/')}
            >
              Weitere Marke
            </button>
          </div>
        </section>
      )}
    </div>
  )
}
