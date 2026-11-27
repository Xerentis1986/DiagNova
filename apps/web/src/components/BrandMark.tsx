import { useTheme } from '../lib/theme'

type Variant = 'symbol' | 'wordmark' | 'lockup'

interface BrandMarkProps {
  variant?: Variant
  className?: string
  /** CSS height for the mark; width follows aspect ratio (kein Abschneiden). */
  height?: string
  priority?: boolean
}

/**
 * Theme-aware DiagNova Marke.
 * Light: charcoal Wordmark (Diag anthrazit / Nova türkis im Raster).
 * Dark: weißes Monochrom-Wordmark (Kontrast).
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
  const symbolSrc = '/brand/symbol.svg'
  const loading = priority ? 'eager' : 'lazy'
  const common = {
    loading: loading as 'eager' | 'lazy',
    decoding: 'async' as const,
    style: { height, width: 'auto', maxWidth: '100%' },
  }

  if (variant === 'symbol') {
    return (
      <img
        src={symbolSrc}
        alt="DiagNova"
        width={128}
        height={128}
        {...common}
        className={`dn-brand-mark dn-brand-mark--symbol ${className}`.trim()}
      />
    )
  }

  if (variant === 'wordmark') {
    return (
      <img
        src={wordmarkSrc}
        alt="DiagNova"
        width={800}
        height={145}
        {...common}
        className={`dn-brand-mark dn-brand-mark--wordmark ${className}`.trim()}
      />
    )
  }

  // lockup = nur Wordmark (kein Symbol neben dem Logo)
  return (
    <img
      src={wordmarkSrc}
      alt="DiagNova"
      width={800}
      height={145}
      {...common}
      className={`dn-brand-mark dn-brand-mark--wordmark ${className}`.trim()}
    />
  )
}
