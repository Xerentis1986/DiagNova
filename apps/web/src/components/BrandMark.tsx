import { useTheme } from '../lib/theme'

type Variant = 'symbol' | 'wordmark' | 'lockup'

interface BrandMarkProps {
  variant?: Variant
  className?: string
  /** Wordmark max height in rem-ish CSS size, e.g. "2.5rem" */
  height?: string
  priority?: boolean
}

/**
 * Theme-aware DiagNova Marke.
 * Light: charcoal Wordmark / Symbol. Dark: weißes Monochrom-Wordmark (Kontrast).
 */
export function BrandMark({
  variant = 'lockup',
  className = '',
  height = '2.25rem',
  priority = false,
}: BrandMarkProps) {
  const { resolved } = useTheme()
  const dark = resolved === 'dark'
  const wordmarkSrc = dark ? '/brand/wordmark-dark.png' : '/brand/wordmark-light.png'
  const symbolSrc = '/brand/symbol-128.png'
  const loading = priority ? 'eager' : 'lazy'

  if (variant === 'symbol') {
    return (
      <img
        src={symbolSrc}
        alt="DiagNova"
        width={128}
        height={128}
        loading={loading}
        decoding="async"
        className={`dn-brand-mark dn-brand-mark--symbol ${className}`.trim()}
        style={{ height, width: 'auto' }}
      />
    )
  }

  if (variant === 'wordmark') {
    return (
      <img
        src={wordmarkSrc}
        alt="DiagNova"
        width={800}
        height={200}
        loading={loading}
        decoding="async"
        className={`dn-brand-mark dn-brand-mark--wordmark ${className}`.trim()}
        style={{ height, width: 'auto' }}
      />
    )
  }

  return (
    <span className={`dn-brand-lockup inline-flex items-center gap-2 ${className}`.trim()}>
      <img
        src={symbolSrc}
        alt=""
        aria-hidden
        width={128}
        height={128}
        loading={loading}
        decoding="async"
        className="dn-brand-mark dn-brand-mark--symbol"
        style={{ height, width: 'auto' }}
      />
      <img
        src={wordmarkSrc}
        alt="DiagNova"
        width={800}
        height={200}
        loading={loading}
        decoding="async"
        className="dn-brand-mark dn-brand-mark--wordmark"
        style={{ height, width: 'auto' }}
      />
    </span>
  )
}
