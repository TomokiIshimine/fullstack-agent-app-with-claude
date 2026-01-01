import React from 'react'
import { cn } from '@/lib/utils/cn'

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
  children: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 focus:ring-primary-300 disabled:bg-primary-300',
  secondary:
    'bg-slate-500 text-white hover:bg-slate-600 active:bg-slate-700 focus:ring-slate-300 disabled:bg-slate-300',
  danger:
    'bg-danger-500 text-white hover:bg-danger-600 active:bg-danger-700 focus:ring-danger-300 disabled:bg-danger-300',
  success:
    'bg-success-500 text-white hover:bg-success-600 active:bg-success-700 focus:ring-success-300 disabled:bg-success-300',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm min-h-[2.25rem]', // 36px min height
  md: 'px-4 py-2 text-base min-h-[2.75rem]', // 44px min height (tap target)
  lg: 'px-6 py-3 text-lg min-h-[3rem]', // 48px min height
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      disabled = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
