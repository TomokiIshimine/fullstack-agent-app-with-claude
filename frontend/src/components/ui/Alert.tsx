import React, { useEffect, useState } from 'react'
import { cn } from '@/lib/utils/cn'
import { CheckIcon, ErrorCircleIcon, WarningIcon, InfoIcon, CloseIcon } from './Icons'

export type AlertVariant = 'success' | 'error' | 'warning' | 'info'

export interface AlertProps {
  variant?: AlertVariant
  children: React.ReactNode
  onDismiss?: () => void
  onRetry?: () => void
  autoCloseMs?: number
  className?: string
}

const variantStyles: Record<
  AlertVariant,
  { container: string; icon: string; iconBg: string; text: string }
> = {
  success: {
    container: 'bg-emerald-50 border-emerald-200',
    icon: 'text-emerald-600',
    iconBg: 'bg-emerald-100',
    text: 'text-emerald-800',
  },
  error: {
    container: 'bg-red-50 border-red-200',
    icon: 'text-red-600',
    iconBg: 'bg-red-100',
    text: 'text-red-800',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200',
    icon: 'text-amber-600',
    iconBg: 'bg-amber-100',
    text: 'text-amber-800',
  },
  info: {
    container: 'bg-blue-50 border-blue-200',
    icon: 'text-blue-600',
    iconBg: 'bg-blue-100',
    text: 'text-blue-800',
  },
}

const icons: Record<AlertVariant, React.ReactNode> = {
  success: <CheckIcon />,
  error: <ErrorCircleIcon />,
  warning: <WarningIcon />,
  info: <InfoIcon />,
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  children,
  onDismiss,
  onRetry,
  autoCloseMs,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    if (autoCloseMs && autoCloseMs > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        onDismiss?.()
      }, autoCloseMs)

      return () => clearTimeout(timer)
    }
  }, [autoCloseMs, onDismiss])

  if (!isVisible) {
    return null
  }

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  const styles = variantStyles[variant]
  const icon = icons[variant]

  return (
    <div
      className={cn('flex items-start gap-3 p-4 border rounded-lg', styles.container, className)}
      role="alert"
    >
      <div className={cn('flex-shrink-0 p-1 rounded-full', styles.iconBg)}>
        <div className={styles.icon}>{icon}</div>
      </div>

      <div className={cn('flex-1', styles.text)}>
        <div className="text-sm">{children}</div>

        {(onRetry || onDismiss) && (
          <div className="mt-3 flex gap-3">
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className={cn(
                  'text-sm font-medium hover:underline focus:outline-none focus:underline',
                  styles.text
                )}
              >
                再試行
              </button>
            )}
            {onDismiss && (
              <button
                type="button"
                onClick={handleDismiss}
                className={cn(
                  'text-sm font-medium hover:underline focus:outline-none focus:underline',
                  styles.text
                )}
              >
                閉じる
              </button>
            )}
          </div>
        )}
      </div>

      {onDismiss && (
        <button
          type="button"
          onClick={handleDismiss}
          className={cn(
            'flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors focus:outline-none focus:bg-black/10',
            styles.icon
          )}
          aria-label="閉じる"
        >
          <CloseIcon />
        </button>
      )}
    </div>
  )
}
