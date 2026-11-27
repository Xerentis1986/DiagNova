import { useEffect, useId, useRef, type ReactNode } from 'react'
import { Button } from './Button'

interface DialogProps {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  actions?: ReactNode
  danger?: boolean
}

export function Dialog({ open, title, children, onClose, actions, danger }: DialogProps) {
  const titleId = useId()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const prev = document.activeElement as HTMLElement | null
    const node = ref.current
    const focusable = node?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusable?.focus()

    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      prev?.focus?.()
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="dn-dialog-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={ref}
        className="dn-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <h2 id={titleId} className={`dn-dialog__title ${danger ? 'text-[var(--dn-danger)]' : ''}`.trim()}>
          {title}
        </h2>
        <div>{children}</div>
        <div className="dn-dialog__actions">
          {actions ?? (
            <Button variant="secondary" onClick={onClose}>
              Schließen
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
