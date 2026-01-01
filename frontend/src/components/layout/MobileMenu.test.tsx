import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithRouter } from '@/test/helpers/renderHelpers'
import { createMockUser } from '@/test/helpers/mockData'
import { MobileMenu } from './MobileMenu'
import type { NavLinkItem } from './Navbar'

describe('MobileMenu', () => {
  const mockOnClose = vi.fn()
  const mockOnLogout = vi.fn()
  const mockUser = createMockUser({ name: 'Test User', email: 'test@example.com' })
  const mockNavLinks: NavLinkItem[] = [
    { path: '/chat', label: 'チャット', icon: 'chat' },
    { path: '/settings', label: '設定', icon: 'settings' },
  ]

  let originalBodyOverflow: string

  beforeEach(() => {
    vi.clearAllMocks()
    originalBodyOverflow = document.body.style.overflow
  })

  afterEach(() => {
    vi.restoreAllMocks()
    document.body.style.overflow = originalBodyOverflow
  })

  const renderMobileMenu = (props?: Partial<Parameters<typeof MobileMenu>[0]>) => {
    return renderWithRouter(
      <MobileMenu
        isOpen={true}
        navLinks={mockNavLinks}
        user={mockUser}
        version="v1.0.0"
        onLogout={mockOnLogout}
        onClose={mockOnClose}
        {...props}
      />,
      { initialEntries: ['/'] }
    )
  }

  describe('Rendering', () => {
    it('should render overlay when open', () => {
      renderMobileMenu({ isOpen: true })

      // Overlay is rendered with fixed inset-0 and bg-black/50
      const overlay = document.querySelector('[aria-hidden="true"]')
      expect(overlay).toBeInTheDocument()
      expect(overlay).toHaveClass('fixed', 'inset-0', 'bg-black/50')
    })

    it('should render menu panel when open', () => {
      renderMobileMenu({ isOpen: true })

      expect(screen.getByRole('navigation', { name: 'モバイルメニュー' })).toBeInTheDocument()
    })

    it('should render brand text', () => {
      renderMobileMenu()

      expect(screen.getByText('AIチャット')).toBeInTheDocument()
    })

    it('should render close button', () => {
      renderMobileMenu()

      expect(screen.getByRole('button', { name: 'メニューを閉じる' })).toBeInTheDocument()
    })

    it('should render avatar with correct letter', () => {
      renderMobileMenu()

      expect(screen.getByText('T')).toBeInTheDocument()
    })

    it('should display user name', () => {
      renderMobileMenu()

      expect(screen.getByText('Test User')).toBeInTheDocument()
    })

    it('should display version when provided', () => {
      renderMobileMenu({ version: 'v2.0.0' })

      expect(screen.getByText('v2.0.0')).toBeInTheDocument()
    })

    it('should not display version when not provided', () => {
      renderMobileMenu({ version: undefined })

      expect(screen.queryByText(/^v\d/)).not.toBeInTheDocument()
    })
  })

  describe('Visibility States', () => {
    it('should apply translate-x-0 when isOpen is true', () => {
      renderMobileMenu({ isOpen: true })

      const menu = screen.getByRole('navigation', { name: 'モバイルメニュー' })
      expect(menu).toHaveClass('translate-x-0')
    })

    it('should apply -translate-x-full when isOpen is false', () => {
      const { container } = renderMobileMenu({ isOpen: false })

      // Use container.querySelector because aria-hidden="true" elements may not be found by getByRole
      const menu = container.querySelector('nav[aria-label="モバイルメニュー"]')
      expect(menu).toBeInTheDocument()
      expect(menu).toHaveClass('-translate-x-full')
    })

    it('should set aria-hidden based on isOpen state', () => {
      const { rerender } = renderWithRouter(
        <MobileMenu
          isOpen={true}
          navLinks={mockNavLinks}
          user={mockUser}
          version="v1.0.0"
          onLogout={mockOnLogout}
          onClose={mockOnClose}
        />,
        { initialEntries: ['/'] }
      )

      const menu = screen.getByRole('navigation', { name: 'モバイルメニュー' })
      expect(menu).toHaveAttribute('aria-hidden', 'false')

      rerender(
        <MobileMenu
          isOpen={false}
          navLinks={mockNavLinks}
          user={mockUser}
          version="v1.0.0"
          onLogout={mockOnLogout}
          onClose={mockOnClose}
        />
      )

      expect(menu).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('Navigation Links', () => {
    it('should render all provided nav links', () => {
      renderMobileMenu()

      expect(screen.getByText('チャット')).toBeInTheDocument()
      expect(screen.getByText('設定')).toBeInTheDocument()
    })

    it('should apply active class to current path link', () => {
      renderWithRouter(
        <MobileMenu
          isOpen={true}
          navLinks={mockNavLinks}
          user={mockUser}
          version="v1.0.0"
          onLogout={mockOnLogout}
          onClose={mockOnClose}
        />,
        { initialEntries: ['/chat'] }
      )

      const chatLink = screen.getByText('チャット').closest('a')
      expect(chatLink).toHaveClass('bg-primary-50', 'text-primary-500')
    })

    it('should call onClose when link is clicked', async () => {
      const user = userEvent.setup()
      renderMobileMenu()

      await user.click(screen.getByText('チャット'))

      expect(mockOnClose).toHaveBeenCalledOnce()
    })
  })

  describe('Close Behavior', () => {
    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      renderMobileMenu()

      await user.click(screen.getByRole('button', { name: 'メニューを閉じる' }))

      expect(mockOnClose).toHaveBeenCalledOnce()
    })

    it('should call onClose when overlay is clicked', async () => {
      const user = userEvent.setup()
      renderMobileMenu()

      const overlay = document.querySelector('[aria-hidden="true"]')
      await user.click(overlay!)

      expect(mockOnClose).toHaveBeenCalledOnce()
    })

    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup()
      renderMobileMenu()

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledOnce()
    })

    it('should not call onClose when Escape is pressed and menu is closed', async () => {
      const user = userEvent.setup()
      renderMobileMenu({ isOpen: false })

      await user.keyboard('{Escape}')

      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })

  describe('Body Scroll Lock', () => {
    it('should set body overflow to hidden when open', () => {
      renderMobileMenu({ isOpen: true })

      expect(document.body.style.overflow).toBe('hidden')
    })

    it('should restore body overflow when closed', () => {
      const { rerender } = renderWithRouter(
        <MobileMenu
          isOpen={true}
          navLinks={mockNavLinks}
          user={mockUser}
          version="v1.0.0"
          onLogout={mockOnLogout}
          onClose={mockOnClose}
        />,
        { initialEntries: ['/'] }
      )

      expect(document.body.style.overflow).toBe('hidden')

      rerender(
        <MobileMenu
          isOpen={false}
          navLinks={mockNavLinks}
          user={mockUser}
          version="v1.0.0"
          onLogout={mockOnLogout}
          onClose={mockOnClose}
        />
      )

      expect(document.body.style.overflow).toBe('')
    })

    it('should cleanup body overflow on unmount', () => {
      const { unmount } = renderMobileMenu({ isOpen: true })

      expect(document.body.style.overflow).toBe('hidden')

      unmount()

      expect(document.body.style.overflow).toBe('')
    })
  })

  describe('Logout', () => {
    it('should render logout button', () => {
      renderMobileMenu()

      expect(screen.getByRole('button', { name: 'ログアウト' })).toBeInTheDocument()
    })

    it('should call onLogout and onClose when logout is clicked', async () => {
      const user = userEvent.setup()
      renderMobileMenu()

      await user.click(screen.getByRole('button', { name: 'ログアウト' }))

      expect(mockOnLogout).toHaveBeenCalledOnce()
      expect(mockOnClose).toHaveBeenCalledOnce()
    })
  })

  describe('Accessibility', () => {
    it('should have aria-label on nav element', () => {
      renderMobileMenu()

      expect(screen.getByRole('navigation', { name: 'モバイルメニュー' })).toBeInTheDocument()
    })

    it('should have aria-label on close button', () => {
      renderMobileMenu()

      expect(screen.getByRole('button', { name: 'メニューを閉じる' })).toBeInTheDocument()
    })

    it('should mark overlay as aria-hidden', () => {
      renderMobileMenu()

      const overlay = document.querySelector('.fixed.inset-0.bg-black\\/50')
      expect(overlay).toHaveAttribute('aria-hidden', 'true')
    })
  })
})
