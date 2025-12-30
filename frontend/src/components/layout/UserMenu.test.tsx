import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithRouter } from '@/test/helpers/renderHelpers'
import { createMockUser } from '@/test/helpers/mockData'
import { UserMenu } from './UserMenu'
import type { NavLinkItem } from './Navbar'

describe('UserMenu', () => {
  const mockOnLogout = vi.fn()
  const mockUser = createMockUser({ name: 'Test User', email: 'test@example.com' })
  const mockNavLinks: NavLinkItem[] = [
    { path: '/chat', label: 'チャット', icon: 'chat' },
    { path: '/settings', label: '設定', icon: 'settings' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  const renderUserMenu = (props?: Partial<Parameters<typeof UserMenu>[0]>) => {
    return renderWithRouter(
      <UserMenu
        user={mockUser}
        navLinks={mockNavLinks}
        onLogout={mockOnLogout}
        version="v1.0.0"
        {...props}
      />,
      { initialEntries: ['/'] }
    )
  }

  describe('Rendering', () => {
    it('should render trigger button with avatar letter', () => {
      renderUserMenu()

      expect(screen.getByText('T')).toBeInTheDocument()
    })

    it('should not render dropdown by default', () => {
      renderUserMenu()

      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })

    it('should display user name in dropdown header', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByText('Test User')).toBeInTheDocument()
    })

    it('should display user email when name exists', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })

    it('should display version when provided', async () => {
      const user = userEvent.setup()
      renderUserMenu({ version: 'v2.0.0' })

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByText('v2.0.0')).toBeInTheDocument()
    })

    it('should not display version when not provided', async () => {
      const user = userEvent.setup()
      renderUserMenu({ version: undefined })

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.queryByText(/^v\d/)).not.toBeInTheDocument()
    })
  })

  describe('Dropdown Toggle', () => {
    it('should open dropdown when trigger is clicked', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('should close dropdown when trigger is clicked again', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      const trigger = screen.getByRole('button', { name: 'ユーザーメニューを開く' })
      await user.click(trigger)
      expect(screen.getByRole('menu')).toBeInTheDocument()

      await user.click(trigger)
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })

    it('should have correct aria-expanded attribute', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      const trigger = screen.getByRole('button', { name: 'ユーザーメニューを開く' })
      expect(trigger).toHaveAttribute('aria-expanded', 'false')

      await user.click(trigger)
      expect(trigger).toHaveAttribute('aria-expanded', 'true')
    })

    it('should have correct aria-haspopup attribute', () => {
      renderUserMenu()

      const trigger = screen.getByRole('button', { name: 'ユーザーメニューを開く' })
      expect(trigger).toHaveAttribute('aria-haspopup', 'menu')
    })
  })

  describe('Navigation Links', () => {
    it('should render all provided nav links', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByRole('menuitem', { name: 'チャット' })).toBeInTheDocument()
      expect(screen.getByRole('menuitem', { name: '設定' })).toBeInTheDocument()
    })

    it('should apply active class to current path link', async () => {
      const user = userEvent.setup()
      renderWithRouter(
        <UserMenu
          user={mockUser}
          navLinks={mockNavLinks}
          onLogout={mockOnLogout}
          version="v1.0.0"
        />,
        { initialEntries: ['/chat'] }
      )

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      const chatLink = screen.getByRole('menuitem', { name: 'チャット' })
      expect(chatLink).toHaveClass('user-menu__nav-item--active')
    })

    it('should close dropdown when link is clicked', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))
      await user.click(screen.getByRole('menuitem', { name: 'チャット' }))

      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Click Outside Behavior', () => {
    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))
      expect(screen.getByRole('menu')).toBeInTheDocument()

      // Click outside
      fireEvent.mouseDown(document.body)

      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Keyboard Navigation', () => {
    it('should close dropdown when Escape key is pressed', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))
      expect(screen.getByRole('menu')).toBeInTheDocument()

      await user.keyboard('{Escape}')

      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Logout', () => {
    it('should render logout button', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByRole('menuitem', { name: 'ログアウト' })).toBeInTheDocument()
    })

    it('should call onLogout when logout is clicked', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))
      await user.click(screen.getByRole('menuitem', { name: 'ログアウト' }))

      expect(mockOnLogout).toHaveBeenCalledOnce()
    })

    it('should close dropdown after logout', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))
      await user.click(screen.getByRole('menuitem', { name: 'ログアウト' }))

      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have role="menu" on dropdown', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('should have role="menuitem" on links and logout button', async () => {
      const user = userEvent.setup()
      renderUserMenu()

      await user.click(screen.getByRole('button', { name: 'ユーザーメニューを開く' }))

      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems.length).toBeGreaterThanOrEqual(3) // 2 links + 1 logout
    })

    it('should have accessible aria-label on trigger', () => {
      renderUserMenu()

      expect(screen.getByRole('button', { name: 'ユーザーメニューを開く' })).toBeInTheDocument()
    })
  })
})
