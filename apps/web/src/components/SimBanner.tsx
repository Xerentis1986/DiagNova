export function SimBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`dn-banner-sim rounded-lg px-3 py-2 text-sm ${compact ? '' : 'mb-4'}`}>
      <strong>Simulierte Daten</strong>
      {!compact && (
        <span>
          {' '}
          – Es findet keine echte Fahrzeugkommunikation statt. Demo/Simulator-Modus.
        </span>
      )}
    </div>
  )
}
