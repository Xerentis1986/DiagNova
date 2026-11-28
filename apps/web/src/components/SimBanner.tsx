export function SimBanner({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`dn-banner-sim rounded-lg px-3 py-2 text-sm ${compact ? '' : 'mb-4'}`}>
      <strong>PILOT</strong>
      {!compact && (
        <span>
          {' '}
          – Demo/Trial. Keine echte Fahrzeugkommunikation als produktiver Claim. Kein kommerzielles
          Voll-GO (Mollie/SMTP/Recht/HW offen).
        </span>
      )}
    </div>
  )
}
