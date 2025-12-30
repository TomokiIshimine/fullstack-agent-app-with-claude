import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithAuthAndRouter } from '@/test/helpers/renderHelpers'
import { createMockUser } from '@/test/helpers/mockData'
import { Navbar } from './Navbar'
import * as authApi from '@/lib/api/auth'

// Mock useLogout hook
const mockHandleLogout = vi.fn()
vi.mock('@/hooks/useLogout', () => ({
  useLogout: () => ({
    handleLogout: mockHandleLogout,
  }),
}))

// Mock useVersion hook
const mockUseVersion = vi.fn(() => ({
  version: 'v1.0.0',
  isLoading: false,
}))
vi.mock('@/hooks/useVersion', () => ({
  useVersion: () => mockUseVersion(),
}))

describe('Navbar', () => {
  const mockUser = createMockUser()
  const mockAdminUser = createMockUser({ role: 'admin' })

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseVersion.mockReturnValue({
      version: 'v1.0.0',
      isLoading: false,
    })
  })

  describe('Rendering', () => {
    it('should not render when user is not authenticated', async () => {
      vi.spyOn(authApi, 'refreshToken').mockRejectedValue(new Error('Not authenticated'))

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      await waitFor(() => {
        expect(screen.queryByRole('banner')).not.toBeInTheDocument()
      })
    })

    it('should render navbar with brand link when authenticated', async () => {
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      expect(await screen.findByRole('link', { name: 'AIチャット' })).toBeInTheDocument()
    })

    it('should render mobile menu toggle button', async () => {
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      expect(await screen.findByRole('button', { name: 'メニューを開く' })).toBeInTheDocument()
    })
  })

  describe('Role-Based Navigation Links', () => {
    it('should render user navigation links for regular user', async () => {
      const user = userEvent.setup()
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      // Wait for navbar to render
      await screen.findByRole('link', { name: 'AIチャット' })

      // Open mobile menu to see nav links
      await user.click(screen.getByRole('button', { name: 'メニューを開く' }))

      expect(await screen.findByText('チャット')).toBeInTheDocument()
      expect(screen.getByText('設定')).toBeInTheDocument()
    })

    it('should render admin navigation links for admin user', async () => {
      const user = userEvent.setup()
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockAdminUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      // Wait for navbar to render
      await screen.findByRole('link', { name: 'AIチャット' })

      // Open mobile menu to see nav links
      await user.click(screen.getByRole('button', { name: 'メニューを開く' }))

      expect(await screen.findByText('ユーザー管理')).toBeInTheDocument()
      expect(screen.getByText('設定')).toBeInTheDocument()
    })

    it('should set home path to /chat for regular user', async () => {
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      const brandLink = await screen.findByRole('link', { name: 'AIチャット' })
      expect(brandLink).toHaveAttribute('href', '/chat')
    })

    it('should set home path to /admin/users for admin', async () => {
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockAdminUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      const brandLink = await screen.findByRole('link', { name: 'AIチャット' })
      expect(brandLink).toHaveAttribute('href', '/admin/users')
    })
  })

  describe('Mobile Menu Toggle', () => {
    it('should open mobile menu when toggle is clicked', async () => {
      const user = userEvent.setup()
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      const toggleButton = await screen.findByRole('button', { name: 'メニューを開く' })
      await user.click(toggleButton)

      expect(
        await screen.findByRole('navigation', { name: 'モバイルメニュー' })
      ).toBeInTheDocument()
    })

    it('should have correct aria-expanded attribute', async () => {
      const user = userEvent.setup()
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      const toggleButton = await screen.findByRole('button', { name: 'メニューを開く' })
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false')

      await user.click(toggleButton)

      await waitFor(() => {
        expect(toggleButton).toHaveAttribute('aria-expanded', 'true')
      })
    })
  })

  describe('Version Display', () => {
    it('should display version in user menu', async () => {
      const user = userEvent.setup()
      mockUseVersion.mockReturnValue({
        version: 'v2.0.0',
        isLoading: false,
      })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      // Wait for navbar to render
      await screen.findByRole('link', { name: 'AIチャット' })

      // Open mobile menu to see version
      await user.click(screen.getByRole('button', { name: 'メニューを開く' }))

      expect(await screen.findByText('v2.0.0')).toBeInTheDocument()
    })
  })

  describe('Logout', () => {
    it('should call handleLogout when logout is clicked', async () => {
      const user = userEvent.setup()
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<Navbar />, {
        mockRefreshToken: false,
      })

      // Wait for navbar to render and open mobile menu
      await screen.findByRole('button', { name: 'メニューを開く' })
      await user.click(screen.getByRole('button', { name: 'メニューを開く' }))

      // Wait for menu to open and click logout
      const logoutButton = await screen.findByRole('button', { name: 'ログアウト' })
      await user.click(logoutButton)

      expect(mockHandleLogout).toHaveBeenCalledOnce()
    })
  })
})
