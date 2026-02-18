import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { SettingsPage } from './SettingsPage'
import { renderWithAuthAndRouter } from '@/test/helpers/renderHelpers'
import { createMockUser } from '@/test/helpers/mockData'
import * as authApi from '@/lib/api/auth'
import * as conversationsApi from '@/lib/api/conversations'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
  },
}))

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock conversations API
    vi.spyOn(conversationsApi, 'fetchConversations').mockResolvedValue({
      conversations: [],
      total: 0,
      page: 1,
      per_page: 20,
      pages: 0,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders settings page with heading', async () => {
      const mockUser = createMockUser({ role: 'user' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: '設定' })).toBeInTheDocument()
      })
    })

    it('renders profile update form', async () => {
      const mockUser = createMockUser({ role: 'user', name: 'Test User' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        expect(screen.getByLabelText('名前')).toBeInTheDocument()
      })
    })

    it('renders password change form', async () => {
      const mockUser = createMockUser({ role: 'user' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        expect(screen.getByLabelText('現在のパスワード')).toBeInTheDocument()
        expect(screen.getByLabelText('新しいパスワード')).toBeInTheDocument()
        expect(screen.getByLabelText('新しいパスワード（確認）')).toBeInTheDocument()
      })
    })
  })

  describe('Admin Layout', () => {
    it('renders without sidebar for admin users', async () => {
      const mockUser = createMockUser({ role: 'admin' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      const { container } = renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: '設定' })).toBeInTheDocument()
      })

      // Admin layout should not have sidebar
      expect(container.querySelector('aside')).not.toBeInTheDocument()
    })
  })

  describe('User Layout', () => {
    it('renders with sidebar for regular users', async () => {
      const mockUser = createMockUser({ role: 'user' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      const { container } = renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: '設定' })).toBeInTheDocument()
      })

      // User layout should have sidebar
      expect(container.querySelector('aside')).toBeInTheDocument()
    })
  })

  describe('Both Forms Present', () => {
    it('renders both profile and password forms', async () => {
      const mockUser = createMockUser({ role: 'user', name: 'Test User' })
      vi.spyOn(authApi, 'refreshToken').mockResolvedValue(mockUser)

      renderWithAuthAndRouter(<SettingsPage />, {
        initialUser: mockUser,
      })

      await waitFor(() => {
        // Profile form
        expect(screen.getByLabelText('名前')).toBeInTheDocument()
        // Password form
        expect(screen.getByLabelText('現在のパスワード')).toBeInTheDocument()
      })
    })
  })
})
