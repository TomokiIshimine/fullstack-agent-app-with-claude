import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useLogout } from '@/hooks/useLogout'
import { useVersion } from '@/hooks/useVersion'
import { getHomePathForRole } from '@/lib/utils/routing'
import { NavIcon, type NavIconType } from './NavIcon'
import { UserMenu } from './UserMenu'
import { MobileMenu } from './MobileMenu'

export interface NavLinkItem {
  path: string
  label: string
  icon?: NavIconType
}

export function Navbar() {
  const { user } = useAuth()
  const { handleLogout } = useLogout()
  const { version } = useVersion()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  if (!user) return null

  const isAdmin = user.role === 'admin'
  const homePath = getHomePathForRole(user.role)

  // Role-based navigation links
  const navLinks: NavLinkItem[] = isAdmin
    ? [
        { path: '/admin/dashboard', label: 'ダッシュボード', icon: 'dashboard' },
        { path: '/admin/users', label: 'ユーザー管理', icon: 'users' },
        { path: '/admin/conversations', label: '会話履歴', icon: 'chat' },
        { path: '/settings', label: '設定', icon: 'settings' },
      ]
    : [
        { path: '/chat', label: 'チャット', icon: 'chat' },
        { path: '/settings', label: '設定', icon: 'settings' },
      ]

  return (
    <header className="navbar">
      <div className="navbar__container">
        {/* Brand */}
        <Link to={homePath} className="navbar__brand">
          AIチャット
        </Link>

        {/* Right Section */}
        <div className="navbar__right">
          {/* Desktop User Menu */}
          <UserMenu user={user} version={version} navLinks={navLinks} onLogout={handleLogout} />

          {/* Mobile Toggle */}
          <button
            type="button"
            className="navbar__mobile-toggle"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="メニューを開く"
            aria-expanded={isMobileMenuOpen}
          >
            <NavIcon icon="menu" size={24} />
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
