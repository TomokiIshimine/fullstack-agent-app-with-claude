import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useLogout } from '@/hooks/useLogout'
import { useVersion } from '@/hooks/useVersion'
import { getHomePathForRole } from '@/lib/utils/routing'
import { UserMenu } from './UserMenu'
import { MobileMenu } from './MobileMenu'

interface NavLinkItem {
  path: string
  label: string
}

export function Navbar() {
  const { user } = useAuth()
  const { handleLogout } = useLogout()
  const { version } = useVersion()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  if (!user) return null

  const isAdmin = user.role === 'admin'
  const homePath = getHomePathForRole(user.role)

  // Role-based navigation links
  const navLinks: NavLinkItem[] = isAdmin
    ? [
        { path: '/admin/users', label: 'ユーザー管理' },
        { path: '/settings', label: '設定' },
      ]
    : [
        { path: '/chat', label: 'チャット' },
        { path: '/settings', label: '設定' },
      ]

  const isActive = (path: string) => {
    if (path === '/chat') {
      return location.pathname === '/chat' || location.pathname.startsWith('/chat/')
    }
    return location.pathname === path
  }

  return (
    <header className="navbar">
      <div className="navbar__container">
        {/* Brand */}
        <Link to={homePath} className="navbar__brand">
          AIチャット
        </Link>

        {/* Desktop Navigation */}
        <nav className="navbar__nav" aria-label="メインナビゲーション">
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`navbar__link ${isActive(link.path) ? 'navbar__link--active' : ''}`}
              aria-current={isActive(link.path) ? 'page' : undefined}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Right Section */}
        <div className="navbar__right">
          {/* Desktop User Menu */}
          <UserMenu user={user} version={version} onLogout={handleLogout} />

          {/* Mobile Toggle */}
          <button
            type="button"
            className="navbar__mobile-toggle"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="メニューを開く"
            aria-expanded={isMobileMenuOpen}
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
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        navLinks={navLinks}
        user={user}
        version={version}
        onLogout={handleLogout}
        onClose={() => setIsMobileMenuOpen(false)}
      />
    </header>
  )
}
