import React, { useState, useCallback, useId } from 'react'
import { cn } from '@/lib/utils/cn'
import { EyeIcon, EyeOffIcon, WarningIcon } from './Icons'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  fullWidth?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    { label, error, helperText, fullWidth = false, type = 'text', className = '', id, ...props },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false)
    const [capsLockOn, setCapsLockOn] = useState(false)

    const isPassword = type === 'password'
    const inputType = isPassword && showPassword ? 'text' : type

    const reactId = useId()
    const inputId = id || reactId

    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (isPassword) {
          setCapsLockOn(e.getModifierState('CapsLock'))
        }
        props.onKeyDown?.(e)
      },
      [isPassword, props]
    )

    const handleKeyUp = useCallback(
      (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (isPassword) {
          setCapsLockOn(e.getModifierState('CapsLock'))
        }
        props.onKeyUp?.(e)
      },
      [isPassword, props]
    )

    const togglePasswordVisibility = () => {
      setShowPassword(prev => !prev)
    }

    return (
      <div className={cn(fullWidth && 'w-full')}>
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-slate-700 mb-1">
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}

        <div className="relative">
          <input
            ref={ref}
            id={inputId}
            type={inputType}
            className={cn(
              'block w-full px-3 py-2 border rounded-lg text-slate-900 placeholder-slate-400',
              'transition-colors duration-200',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              'disabled:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-500',
              'min-h-[2.75rem]', // 44px tap target
              error
                ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                : 'border-slate-300 focus:border-blue-500 focus:ring-blue-200',
              isPassword && 'pr-10',
              className
            )}
            onKeyDown={handleKeyDown}
            onKeyUp={handleKeyUp}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            {...props}
          />

          {isPassword && (
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-slate-700 focus:outline-none focus:text-slate-700 transition-colors"
              aria-label={showPassword ? 'パスワードを隠す' : 'パスワードを表示'}
              tabIndex={-1}
            >
              {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          )}
        </div>

        {capsLockOn && isPassword && (
          <p className="mt-1 text-sm text-amber-600 flex items-center gap-1" role="alert">
            <WarningIcon className="w-4 h-4" />
            Caps Lock がオンになっています
          </p>
        )}

        {error && (
          <p id={`${inputId}-error`} className="mt-1 text-sm text-red-600" role="alert">
            {error}
          </p>
        )}

        {!error && helperText && (
          <p id={`${inputId}-helper`} className="mt-1 text-sm text-slate-500">
            {helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
