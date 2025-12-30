import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { User } from '@/types/auth'
import { isPathActive } from '@/lib/utils/routing'
import { getDisplayName, getAvatarLetter } from '@/lib/utils/user'
import { useScrollLock } from '@/hooks/useScrollLock'
import { NavIcon } from './NavIcon'
import type { NavLinkItem } from './Navbar'

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
            <NavIcon icon="close" size={24} />
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
              className={`mobile-menu__link ${isPathActive(location.pathname, link.path) ? 'mobile-menu__link--active' : ''}`}
              onClick={onClose}
            >
              {link.icon && <NavIcon icon={link.icon} size={20} />}
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
