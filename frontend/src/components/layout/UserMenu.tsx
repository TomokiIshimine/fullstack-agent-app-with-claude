import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { User } from '@/types/auth'

interface UserMenuProps {
  user: User
  version?: string
  onLogout: () => void
}

export function UserMenu({ user, version, onLogout }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const displayName = user.name || user.email
  const avatarLetter = (user.name?.[0] || user.email[0] || 'U').toUpperCase()

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
        <svg
          className={`user-menu__chevron ${isOpen ? 'user-menu__chevron--open' : ''}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className="user-menu__dropdown" role="menu">
          <div className="user-menu__header">
            {version && <div className="user-menu__version">{version}</div>}
            <div className="user-menu__name">{displayName}</div>
            {user.name && <div className="user-menu__email">{user.email}</div>}
          </div>

          <Link
            to="/settings"
            className="user-menu__item"
            role="menuitem"
            onClick={() => setIsOpen(false)}
          >
            設定
          </Link>

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
            ログアウト
          </button>
        </div>
      )}
    </div>
  )
}
