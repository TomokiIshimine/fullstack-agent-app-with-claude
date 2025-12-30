import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Modal } from './Modal'

// Mock useScrollLock hook
vi.mock('@/hooks/useScrollLock', () => ({
  useScrollLock: vi.fn(),
}))

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('renders children when open', () => {
      render(
        <Modal {...defaultProps}>
          <div>Modal content</div>
        </Modal>
      )
      expect(screen.getByText('Modal content')).toBeInTheDocument()
    })

    it('does not render when closed', () => {
      render(
        <Modal {...defaultProps} isOpen={false}>
          <div>Modal content</div>
        </Modal>
      )
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
    })

    it('renders with title', () => {
      render(
        <Modal {...defaultProps} title="Modal Title">
          Content
        </Modal>
      )
      expect(screen.getByText('Modal Title')).toBeInTheDocument()
    })

    it('renders footer when provided', () => {
      render(
        <Modal {...defaultProps} footer={<button>Submit</button>}>
          Content
        </Modal>
      )
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = render(
        <Modal {...defaultProps} size="sm">
          Content
        </Modal>
      )
      expect(container.querySelector('.max-w-md')).toBeInTheDocument()
    })

    it('renders medium size (default)', () => {
      const { container } = render(<Modal {...defaultProps}>Content</Modal>)
      expect(container.querySelector('.max-w-lg')).toBeInTheDocument()
    })

    it('renders large size', () => {
      const { container } = render(
        <Modal {...defaultProps} size="lg">
          Content
        </Modal>
      )
      expect(container.querySelector('.max-w-2xl')).toBeInTheDocument()
    })
  })

  describe('Close Button', () => {
    it('shows close button by default', () => {
      render(<Modal {...defaultProps}>Content</Modal>)
      expect(screen.getByLabelText('閉じる')).toBeInTheDocument()
    })

    it('hides close button when showCloseButton is false', () => {
      render(
        <Modal {...defaultProps} showCloseButton={false}>
          Content
        </Modal>
      )
      expect(screen.queryByLabelText('閉じる')).not.toBeInTheDocument()
    })

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          Content
        </Modal>
      )

      await user.click(screen.getByLabelText('閉じる'))
      expect(handleClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Outside Click', () => {
    it('closes on outside click by default', () => {
      const handleClose = vi.fn()
      const { container } = render(
        <Modal isOpen={true} onClose={handleClose}>
          Content
        </Modal>
      )

      // Click directly on the overlay (the element with the fixed class)
      const overlay = container.querySelector('.fixed.inset-0')
      fireEvent.click(overlay!)
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('does not close on outside click when closeOnOutsideClick is false', () => {
      const handleClose = vi.fn()
      const { container } = render(
        <Modal isOpen={true} onClose={handleClose} closeOnOutsideClick={false}>
          Content
        </Modal>
      )

      const overlay = container.querySelector('.fixed.inset-0')
      fireEvent.click(overlay!)
      expect(handleClose).not.toHaveBeenCalled()
    })

    it('does not close when clicking inside modal content', async () => {
      const user = userEvent.setup()
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          <button>Inside Button</button>
        </Modal>
      )

      await user.click(screen.getByRole('button', { name: 'Inside Button' }))
      expect(handleClose).not.toHaveBeenCalled()
    })
  })

  describe('Escape Key', () => {
    it('closes on Escape key press', () => {
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          Content
        </Modal>
      )

      fireEvent.keyDown(document, { key: 'Escape' })
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('does not call onClose on Escape when modal is closed', () => {
      const handleClose = vi.fn()
      render(
        <Modal isOpen={false} onClose={handleClose}>
          Content
        </Modal>
      )

      fireEvent.keyDown(document, { key: 'Escape' })
      expect(handleClose).not.toHaveBeenCalled()
    })

    it('does not call onClose on other key presses', () => {
      const handleClose = vi.fn()
      render(
        <Modal isOpen={true} onClose={handleClose}>
          Content
        </Modal>
      )

      fireEvent.keyDown(document, { key: 'Enter' })
      expect(handleClose).not.toHaveBeenCalled()
    })
  })

  describe('Header', () => {
    it('renders header when title is provided', () => {
      render(
        <Modal {...defaultProps} title="Test Title">
          Content
        </Modal>
      )
      expect(screen.getByRole('heading', { name: 'Test Title' })).toBeInTheDocument()
    })

    it('renders header when only close button is shown', () => {
      render(
        <Modal {...defaultProps} showCloseButton={true}>
          Content
        </Modal>
      )
      expect(screen.getByLabelText('閉じる')).toBeInTheDocument()
    })

    it('does not render header when no title and close button is hidden', () => {
      const { container } = render(
        <Modal {...defaultProps} showCloseButton={false}>
          Content
        </Modal>
      )
      expect(container.querySelector('.border-b')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has dialog role', () => {
      render(<Modal {...defaultProps}>Content</Modal>)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('has aria-modal attribute', () => {
      render(<Modal {...defaultProps}>Content</Modal>)
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
    })

    it('has aria-labelledby when title is provided', () => {
      render(
        <Modal {...defaultProps} title="Modal Title">
          Content
        </Modal>
      )
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'modal-title')
    })

    it('does not have aria-labelledby when no title', () => {
      render(<Modal {...defaultProps}>Content</Modal>)
      expect(screen.getByRole('dialog')).not.toHaveAttribute('aria-labelledby')
    })

    it('close button has accessible label', () => {
      render(<Modal {...defaultProps}>Content</Modal>)
      expect(screen.getByLabelText('閉じる')).toBeInTheDocument()
    })
  })

  describe('Event Listener Cleanup', () => {
    it('removes escape key listener on unmount', () => {
      const handleClose = vi.fn()
      const { unmount } = render(
        <Modal isOpen={true} onClose={handleClose}>
          Content
        </Modal>
      )

      unmount()

      fireEvent.keyDown(document, { key: 'Escape' })
      expect(handleClose).not.toHaveBeenCalled()
    })
  })
})
