import React, { useEffect, useRef } from 'react'
import { useScrollLock } from '@/hooks/useScrollLock'
import { cn } from '@/lib/utils/cn'
import { CloseIcon } from './Icons'

export type ModalSize = 'sm' | 'md' | 'lg'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  size?: ModalSize
  closeOnOutsideClick?: boolean
  showCloseButton?: boolean
  children: React.ReactNode
  footer?: React.ReactNode
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'md',
  closeOnOutsideClick = true,
  showCloseButton = true,
  children,
  footer,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null)

  // Prevent body scroll when modal is open
  useScrollLock(isOpen)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) {
    return null
  }

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOutsideClick && e.target === overlayRef.current) {
      onClose()
    }
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-fade-in"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div
        className={cn(
          'bg-white rounded-xl shadow-2xl w-full max-h-[90vh] flex flex-col animate-scale-in',
          sizeStyles[size]
        )}
      >
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            {title && (
              <h2 id="modal-title" className="text-xl font-semibold text-slate-900">
                {title}
              </h2>
            )}
            {!title && <div />}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="閉じる"
              >
                <CloseIcon className="w-6 h-6" />
              </button>
            )}
          </div>
        )}

        <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>

        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
