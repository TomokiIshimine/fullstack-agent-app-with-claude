import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginPage } from './LoginPage'
import { renderWithRouter } from '@/test/helpers/renderHelpers'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn().mockResolvedValue({ id: 1, email: 'test@example.com', role: 'user' }),
  }),
}))

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders login form', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByRole('heading', { name: 'ログイン' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'ログイン' })).toBeInTheDocument()
    })

    it('renders email input', () => {
      renderWithRouter(<LoginPage />)

      const emailInput = screen.getByRole('textbox')
      expect(emailInput).toHaveAttribute('type', 'email')
      expect(emailInput).toHaveAttribute('autocomplete', 'email')
    })

    it('renders password input', () => {
      const { container } = renderWithRouter(<LoginPage />)

      const passwordInput = container.querySelector('input[type="password"]')
      expect(passwordInput).toBeInTheDocument()
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })
  })

  describe('User Input', () => {
    it('allows user to type email and password', async () => {
      const user = userEvent.setup()
      const { container } = renderWithRouter(<LoginPage />)

      const emailInput = screen.getByRole('textbox')
      const passwordInput = container.querySelector('input[type="password"]') as HTMLInputElement

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      expect(emailInput).toHaveValue('test@example.com')
      expect(passwordInput).toHaveValue('password123')
    })
  })

  describe('Session Expired Message', () => {
    it('shows session expired message when expired query param is present', () => {
      renderWithRouter(<LoginPage />, {
        initialEntries: ['/login?expired=true'],
      })

      expect(
        screen.getByText('セッションが切れました。再度ログインしてください。')
      ).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('submit button is accessible', () => {
      renderWithRouter(<LoginPage />)
      expect(screen.getByRole('button', { name: 'ログイン' })).toBeInTheDocument()
    })

    it('form inputs are present', () => {
      const { container } = renderWithRouter(<LoginPage />)

      expect(screen.getByRole('textbox')).toBeInTheDocument()
      expect(container.querySelector('input[type="password"]')).toBeInTheDocument()
    })
  })
})
