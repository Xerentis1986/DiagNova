import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'danger-outline'
type Size = 'md' | 'sm'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  children: ReactNode
}

const VARIANT: Record<Variant, string> = {
  primary: 'dn-btn--primary',
  secondary: 'dn-btn--secondary',
  ghost: 'dn-btn--ghost',
  danger: 'dn-btn--danger',
  'danger-outline': 'dn-btn--danger-outline',
}

export function Button({
  variant = 'secondary',
  size = 'md',
  className = '',
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`dn-btn ${VARIANT[variant]} ${size === 'sm' ? 'dn-btn--sm' : ''} ${className}`.trim()}
      {...rest}
    >
      {children}
    </button>
  )
}
