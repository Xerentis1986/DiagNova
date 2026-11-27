import type { ReactNode } from 'react'

export function Panel({
  children,
  className = '',
  as: Tag = 'section',
}: {
  children: ReactNode
  className?: string
  as?: 'section' | 'div' | 'article'
}) {
  return <Tag className={`dn-panel p-4 ${className}`.trim()}>{children}</Tag>
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: ReactNode
  actions?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="dn-page-title">{title}</h1>
        {description && <div className="mt-1 max-w-2xl text-sm text-[var(--dn-muted)]">{description}</div>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function SectionTitle({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <h2 id={id} className="dn-section-title">
      {children}
    </h2>
  )
}

export function Badge({
  children,
  tone = 'default',
}: {
  children: ReactNode
  tone?: 'default' | 'ok' | 'warn' | 'danger' | 'accent'
}) {
  const cls =
    tone === 'ok'
      ? 'dn-badge--ok'
      : tone === 'warn'
        ? 'dn-badge--warn'
        : tone === 'danger'
          ? 'dn-badge--danger'
          : tone === 'accent'
            ? 'dn-badge--accent'
            : ''
  return <span className={`dn-badge ${cls}`.trim()}>{children}</span>
}
