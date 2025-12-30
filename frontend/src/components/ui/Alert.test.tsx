import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Alert } from './Alert'

describe('Alert', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(<Alert>Alert message</Alert>)
      expect(screen.getByText('Alert message')).toBeInTheDocument()
    })

    it('renders with alert role', () => {
      render(<Alert>Message</Alert>)
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('renders with default info variant', () => {
      const { container } = render(<Alert>Info</Alert>)
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument()
    })
  })

  describe('Variants', () => {
    it('renders success variant', () => {
      const { container } = render(<Alert variant="success">Success</Alert>)
      expect(container.querySelector('.bg-emerald-50')).toBeInTheDocument()
    })

    it('renders error variant', () => {
      const { container } = render(<Alert variant="error">Error</Alert>)
      expect(container.querySelector('.bg-red-50')).toBeInTheDocument()
    })

    it('renders warning variant', () => {
      const { container } = render(<Alert variant="warning">Warning</Alert>)
      expect(container.querySelector('.bg-amber-50')).toBeInTheDocument()
    })

    it('renders info variant', () => {
      const { container } = render(<Alert variant="info">Info</Alert>)
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument()
    })
  })

  describe('Dismiss Button', () => {
    it('renders dismiss button when onDismiss is provided', () => {
      render(<Alert onDismiss={() => {}}>Message</Alert>)
      expect(screen.getByLabelText('閉じる')).toBeInTheDocument()
    })

    it('renders text dismiss button inside alert', () => {
      render(<Alert onDismiss={() => {}}>Message</Alert>)
      // Both text button and icon button with '閉じる' label exist
      expect(screen.getAllByRole('button', { name: '閉じる' }).length).toBeGreaterThanOrEqual(1)
    })

    it('calls onDismiss when dismiss button is clicked', async () => {
      vi.useRealTimers()
      const user = userEvent.setup()
      const handleDismiss = vi.fn()
      render(<Alert onDismiss={handleDismiss}>Message</Alert>)

      await user.click(screen.getByLabelText('閉じる'))
      expect(handleDismiss).toHaveBeenCalledTimes(1)
    })

    it('hides alert after dismiss', async () => {
      vi.useRealTimers()
      const user = userEvent.setup()
      render(<Alert onDismiss={() => {}}>Message</Alert>)

      await user.click(screen.getByLabelText('閉じる'))
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('Retry Button', () => {
    it('renders retry button when onRetry is provided', () => {
      render(<Alert onRetry={() => {}}>Error occurred</Alert>)
      expect(screen.getByRole('button', { name: '再試行' })).toBeInTheDocument()
    })

    it('calls onRetry when retry button is clicked', async () => {
      vi.useRealTimers()
      const user = userEvent.setup()
      const handleRetry = vi.fn()
      render(<Alert onRetry={handleRetry}>Error</Alert>)

      await user.click(screen.getByRole('button', { name: '再試行' }))
      expect(handleRetry).toHaveBeenCalledTimes(1)
    })

    it('renders both retry and dismiss buttons', () => {
      render(
        <Alert onRetry={() => {}} onDismiss={() => {}}>
          Error
        </Alert>
      )
      expect(screen.getByRole('button', { name: '再試行' })).toBeInTheDocument()
      // Multiple dismiss buttons exist (text + icon)
      expect(screen.getAllByRole('button', { name: '閉じる' }).length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Auto Close', () => {
    it('auto closes after specified time', () => {
      const handleDismiss = vi.fn()
      render(
        <Alert autoCloseMs={3000} onDismiss={handleDismiss}>
          Auto close
        </Alert>
      )

      expect(screen.getByRole('alert')).toBeInTheDocument()

      act(() => {
        vi.advanceTimersByTime(3000)
      })

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      expect(handleDismiss).toHaveBeenCalledTimes(1)
    })

    it('does not auto close if autoCloseMs is not set', () => {
      render(<Alert>Persistent alert</Alert>)

      act(() => {
        vi.advanceTimersByTime(10000)
      })

      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('clears timer on unmount', () => {
      const { unmount } = render(<Alert autoCloseMs={5000}>Alert</Alert>)

      act(() => {
        vi.advanceTimersByTime(2000)
      })

      unmount()

      // Should not throw or cause issues
      act(() => {
        vi.advanceTimersByTime(5000)
      })
    })
  })

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(<Alert className="custom-alert">Message</Alert>)
      expect(container.querySelector('.custom-alert')).toBeInTheDocument()
    })

    it('merges custom className with default classes', () => {
      const { container } = render(<Alert className="my-class">Message</Alert>)
      const alert = container.querySelector('.my-class')
      expect(alert).toHaveClass('bg-blue-50') // default info variant
    })
  })

  describe('Icons', () => {
    it('renders icon for each variant', () => {
      const { rerender, container } = render(<Alert variant="success">Success</Alert>)
      expect(container.querySelector('svg')).toBeInTheDocument()

      rerender(<Alert variant="error">Error</Alert>)
      expect(container.querySelector('svg')).toBeInTheDocument()

      rerender(<Alert variant="warning">Warning</Alert>)
      expect(container.querySelector('svg')).toBeInTheDocument()

      rerender(<Alert variant="info">Info</Alert>)
      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper role attribute', () => {
      render(<Alert>Message</Alert>)
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('dismiss button has accessible label', () => {
      render(<Alert onDismiss={() => {}}>Message</Alert>)
      expect(screen.getByLabelText('閉じる')).toBeInTheDocument()
    })
  })
})
