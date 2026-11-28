import { useTheme } from '../lib/theme'
import type { ThemePreference } from '../lib/api'

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: 'light', label: 'Hell' },
  { value: 'dark', label: 'Dunkel' },
  { value: 'system', label: 'System' },
]

export function ThemeToggle() {
  const { preference, setPreference } = useTheme()

  return (
    <div
      className="inline-flex rounded-md border border-[var(--dn-border)] p-0.5"
      role="group"
      aria-label="Theme"
    >
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          aria-pressed={preference === opt.value}
          className={`rounded px-2.5 py-1 text-xs ${
            preference === opt.value
              ? 'bg-[var(--dn-accent)] text-white'
              : 'text-[var(--dn-muted)] hover:bg-[var(--dn-hover)] hover:text-[var(--dn-text)]'
          }`}
          onClick={() => void setPreference(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
