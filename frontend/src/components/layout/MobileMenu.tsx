import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { User } from '@/types/auth'
import { isPathActive } from '@/lib/utils/routing'
import { getDisplayName, getAvatarLetter } from '@/lib/utils/user'
import { useScrollLock } from '@/hooks/useScrollLock'
import { cn } from '@/lib/utils/cn'
import { NavIcon } from './NavIcon'
import type { NavLinkItem } from './Navbar'

/**
 * Close button styles for mobile menu header
 */
const closeButtonStyles = {
  base: 'flex items-center justify-center w-10 h-10 p-0 border-none bg-transparent rounded-lg cursor-pointer',
  color: 'text-slate-500',
  transition: 'transition-colors duration-200',
  hover: 'hover:bg-slate-100 hover:text-slate-800',
  focus: 'focus:outline-none focus:ring-2 focus:ring-primary-500',
} as const

/**
 * Logout button styles for mobile menu footer
 */
const logoutButtonStyles = {
  base: 'flex items-center w-full px-6 py-3.5 text-[15px] bg-transparent border-none cursor-pointer text-left',
  color: 'text-danger-600',
  transition: 'transition-colors duration-200',
  hover: 'hover:bg-danger-50',
  focus: 'focus:outline-none focus:bg-danger-100',
} as const

interface MobileMenuProps {
  isOpen: boolean
  navLinks: NavLinkItem[]
  user: User
  version?: string
  onLogout: () => void
  onClose: () => void
}

export function MobileMenu({
  isOpen,
  navLinks,
  user,
  version,
  onLogout,
  onClose,
}: MobileMenuProps) {
  const location = useLocation()

  const displayName = getDisplayName(user)
  const avatarLetter = getAvatarLetter(user)

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Prevent body scroll when menu is open
  useScrollLock(isOpen)

  return (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 bg-black/50 z-[150] transition-all duration-300 md:hidden ${
          isOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Menu */}
      <nav
        className={`fixed left-0 top-0 bottom-0 w-[280px] max-w-[85vw] bg-white z-[200] flex flex-col shadow-lg transition-transform duration-300 ease-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="モバイルメニュー"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <span className="text-lg font-semibold text-slate-800">AIチャット</span>
          <button
            type="button"
            className={cn(
              closeButtonStyles.base,
              closeButtonStyles.color,
              closeButtonStyles.transition,
              closeButtonStyles.hover,
              closeButtonStyles.focus
            )}
            onClick={onClose}
            aria-label="メニューを閉じる"
          >
            <NavIcon icon="close" size={24} />
          </button>
        </div>

        {/* User Info */}
        <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-200">
          <div className="w-10 h-10 rounded-full bg-primary-500 text-white flex items-center justify-center text-base font-semibold shrink-0">
            {avatarLetter}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-medium text-slate-800 truncate">{displayName}</div>
            {version && <div className="text-xs text-slate-400">{version}</div>}
          </div>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 py-2 overflow-y-auto">
          {navLinks.map(link => {
            const isActive = isPathActive(location.pathname, link.path)
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-3 px-6 py-3.5 text-[15px] no-underline transition-colors duration-200 ${
                  isActive
                    ? 'bg-primary-50 text-primary-500 font-medium'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                } focus:outline-none focus:bg-slate-100`}
                onClick={onClose}
              >
                {link.icon && <NavIcon icon={link.icon} size={20} />}
                {link.label}
              </Link>
            )
          })}
        </div>

        {/* Footer with Logout */}
        <div className="py-2 border-t border-slate-200">
          <button
            type="button"
            className={cn(
              logoutButtonStyles.base,
              logoutButtonStyles.color,
              logoutButtonStyles.transition,
              logoutButtonStyles.hover,
              logoutButtonStyles.focus
            )}
            onClick={() => {
              onLogout()
              onClose()
            }}
          >
            ログアウト
          </button>
        </div>
      </nav>
    </>
  )
}
