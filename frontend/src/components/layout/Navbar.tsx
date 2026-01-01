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
    <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-slate-200 z-[100]">
      <div className="h-full flex items-center justify-between px-4">
        {/* Brand */}
        <Link
          to={homePath}
          className="text-xl font-semibold text-slate-800 no-underline transition-colors duration-200 hover:text-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
        >
          AIチャット
        </Link>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Desktop User Menu */}
          <UserMenu user={user} version={version} navLinks={navLinks} onLogout={handleLogout} />

          {/* Mobile Toggle */}
          <button
            type="button"
            className="hidden md:hidden items-center justify-center w-11 h-11 p-0 border-none bg-transparent rounded-lg cursor-pointer text-slate-600 transition-colors duration-200 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 max-md:flex"
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
