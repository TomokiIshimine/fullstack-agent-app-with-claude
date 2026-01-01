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
    <div className="relative max-md:hidden" ref={menuRef}>
      <button
        type="button"
        className="flex items-center gap-2 p-1.5 border-none bg-transparent rounded-lg cursor-pointer transition-colors duration-200 min-h-11 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label="ユーザーメニューを開く"
      >
        <div className="w-8 h-8 rounded-full bg-primary-500 text-white flex items-center justify-center text-sm font-semibold">
          {avatarLetter}
        </div>
        <NavIcon
          icon="chevron"
          className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 min-w-[220px] bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden z-50"
          role="menu"
        >
          <div className="px-4 py-3 border-b border-slate-200">
            {version && <div className="text-xs text-slate-400 mb-1">{version}</div>}
            <div className="text-sm font-medium text-slate-800 break-all">{displayName}</div>
            {user.name && <div className="text-xs text-slate-500 break-all">{user.email}</div>}
          </div>

          <div className="py-2">
            {navLinks.map(link => {
              const isActive = isPathActive(location.pathname, link.path)
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-3 w-full px-4 py-3 text-left text-sm no-underline transition-colors duration-200 ${
                    isActive
                      ? 'bg-primary-50 text-primary-500 hover:bg-primary-100'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                  } focus:outline-none focus:bg-slate-100`}
                  role="menuitem"
                  onClick={() => setIsOpen(false)}
                >
                  {link.icon && <NavIcon icon={link.icon} />}
                  {link.label}
                </Link>
              )
            })}
          </div>

          <div className="h-px bg-slate-200" />

          <button
            type="button"
            className="flex items-center gap-3 w-full px-4 py-3 text-left text-sm text-danger-600 bg-transparent border-none cursor-pointer transition-colors duration-200 hover:bg-danger-50 focus:outline-none focus:bg-slate-100"
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
