import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

interface FieldProps {
  label: string
  htmlFor?: string
  hint?: string
  error?: string
  children: ReactNode
  className?: string
}

export function Field({ label, htmlFor, hint, error, children, className = '' }: FieldProps) {
  return (
    <label className={`dn-field ${className}`.trim()} htmlFor={htmlFor}>
      <span className="dn-label">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-[var(--dn-muted)]">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-[var(--dn-danger)]">{error}</span>}
    </label>
  )
}

export function Input({ className = '', ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`dn-input w-full ${className}`.trim()} {...rest} />
}

export function TextArea({ className = '', ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`dn-input w-full ${className}`.trim()} {...rest} />
}

export function Select({ className = '', children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`dn-input w-full ${className}`.trim()} {...rest}>
      {children}
    </select>
  )
}
