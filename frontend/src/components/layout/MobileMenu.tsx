import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { User } from '@/types/auth'

interface NavLinkItem {
  path: string
  label: string
}

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

  const displayName = user.name || user.email
  const avatarLetter = (user.name?.[0] || user.email[0] || 'U').toUpperCase()

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
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const isActive = (path: string) => {
    if (path === '/chat') {
      return location.pathname === '/chat' || location.pathname.startsWith('/chat/')
    }
    return location.pathname === path
  }

  return (
    <>
      {/* Overlay */}
      <div
        className={`mobile-menu__overlay ${isOpen ? 'mobile-menu__overlay--open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Menu */}
      <nav
        className={`mobile-menu ${isOpen ? 'mobile-menu--open' : ''}`}
        aria-label="モバイルメニュー"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="mobile-menu__header">
          <span className="mobile-menu__brand">AIチャット</span>
          <button
            type="button"
            className="mobile-menu__close"
            onClick={onClose}
            aria-label="メニューを閉じる"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* User Info */}
        <div className="mobile-menu__user">
          <div className="mobile-menu__avatar">{avatarLetter}</div>
          <div className="mobile-menu__user-info">
            <div className="mobile-menu__user-name">{displayName}</div>
            {version && <div className="mobile-menu__version">{version}</div>}
          </div>
        </div>

        {/* Navigation Links */}
        <div className="mobile-menu__nav">
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`mobile-menu__link ${isActive(link.path) ? 'mobile-menu__link--active' : ''}`}
              onClick={onClose}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Footer with Logout */}
        <div className="mobile-menu__footer">
          <button
            type="button"
            className="mobile-menu__logout"
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
