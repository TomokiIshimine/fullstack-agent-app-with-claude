import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { User } from '@/types/auth'
import { isPathActive } from '@/lib/utils/routing'
import { getDisplayName, getAvatarLetter } from '@/lib/utils/user'
import { NavIcon } from './NavIcon'
import type { NavLinkItem } from './Navbar'

interface UserMenuProps {
  user: User
  version?: string
  navLinks: NavLinkItem[]
  onLogout: () => void
}

export function UserMenu({ user, version, navLinks, onLogout }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const location = useLocation()

  const displayName = getDisplayName(user)
  const avatarLetter = getAvatarLetter(user)

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        type="button"
        className="user-menu__trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label="ユーザーメニューを開く"
      >
        <div className="user-menu__avatar">{avatarLetter}</div>
        <NavIcon
          icon="chevron"
          className={`user-menu__chevron ${isOpen ? 'user-menu__chevron--open' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="user-menu__dropdown" role="menu">
          <div className="user-menu__header">
            {version && <div className="user-menu__version">{version}</div>}
            <div className="user-menu__name">{displayName}</div>
            {user.name && <div className="user-menu__email">{user.email}</div>}
          </div>

          <div className="user-menu__nav">
            {navLinks.map(link => (
              <Link
                key={link.path}
                to={link.path}
                className={`user-menu__nav-item ${isPathActive(location.pathname, link.path) ? 'user-menu__nav-item--active' : ''}`}
                role="menuitem"
                onClick={() => setIsOpen(false)}
              >
                {link.icon && <NavIcon icon={link.icon} />}
                {link.label}
              </Link>
            ))}
          </div>

          <div className="user-menu__divider" />

          <button
            type="button"
            className="user-menu__item user-menu__item--danger"
            role="menuitem"
            onClick={() => {
              onLogout()
              setIsOpen(false)
            }}
          >
            <NavIcon icon="logout" />
            ログアウト
          </button>
        </div>
      )}
    </div>
  )
}
