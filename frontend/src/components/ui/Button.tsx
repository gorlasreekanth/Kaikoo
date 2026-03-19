import { cn } from '../../utils/cn'
import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  loading?: boolean
}

export function Button({ variant = 'primary', size = 'md', loading, className, children, disabled, ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        size === 'md' && 'px-4 py-2 text-sm',
        size === 'sm' && 'px-3 py-1.5 text-xs',
        variant === 'primary' && 'bg-accent text-white hover:bg-accent-hover',
        variant === 'ghost' && 'bg-transparent text-text-muted hover:text-text hover:bg-muted',
        variant === 'danger' && 'bg-danger/10 text-danger hover:bg-danger/20',
        className
      )}
      {...props}
    >
      {loading && (
        <span className="size-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  )
}
