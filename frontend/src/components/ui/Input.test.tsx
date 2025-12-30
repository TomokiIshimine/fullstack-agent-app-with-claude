import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from './Input'

describe('Input', () => {
  describe('Rendering', () => {
    it('renders input element', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('renders with label', () => {
      render(<Input label="Email" />)
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
    })

    it('renders label with required indicator', () => {
      render(<Input label="Email" required />)
      expect(screen.getByText('*')).toBeInTheDocument()
    })

    it('renders helper text', () => {
      render(<Input helperText="Enter your email address" />)
      expect(screen.getByText('Enter your email address')).toBeInTheDocument()
    })

    it('does not render helper text when error exists', () => {
      render(<Input helperText="Helper" error="Error message" />)
      expect(screen.queryByText('Helper')).not.toBeInTheDocument()
      expect(screen.getByText('Error message')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('displays error message', () => {
      render(<Input error="Invalid email" />)
      expect(screen.getByText('Invalid email')).toBeInTheDocument()
    })

    it('applies error styles to input', () => {
      render(<Input error="Error" />)
      expect(screen.getByRole('textbox')).toHaveClass('border-red-300')
    })

    it('sets aria-invalid when error exists', () => {
      render(<Input error="Error" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
    })

    it('sets aria-invalid to false when no error', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'false')
    })

    it('links error message with aria-describedby', () => {
      render(<Input id="email" error="Invalid email" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'email-error')
    })
  })

  describe('fullWidth', () => {
    it('does not have full width by default', () => {
      const { container } = render(<Input />)
      expect(container.firstChild).not.toHaveClass('w-full')
    })

    it('has full width when fullWidth is true', () => {
      const { container } = render(<Input fullWidth />)
      expect(container.firstChild).toHaveClass('w-full')
    })
  })

  describe('Password Input', () => {
    it('renders password input with visibility toggle', () => {
      render(<Input type="password" label="Password" />)
      expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password')
      expect(screen.getByLabelText('パスワードを表示')).toBeInTheDocument()
    })

    it('toggles password visibility', async () => {
      const user = userEvent.setup()
      render(<Input type="password" label="Password" />)

      const input = screen.getByLabelText('Password')
      expect(input).toHaveAttribute('type', 'password')

      await user.click(screen.getByLabelText('パスワードを表示'))
      expect(input).toHaveAttribute('type', 'text')
      expect(screen.getByLabelText('パスワードを隠す')).toBeInTheDocument()

      await user.click(screen.getByLabelText('パスワードを隠す'))
      expect(input).toHaveAttribute('type', 'password')
    })
  })

  describe('User Input', () => {
    it('handles user typing', async () => {
      const user = userEvent.setup()
      render(<Input label="Name" />)

      const input = screen.getByLabelText('Name')
      await user.type(input, 'John Doe')

      expect(input).toHaveValue('John Doe')
    })

    it('calls onChange handler', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      render(<Input label="Name" onChange={handleChange} />)

      await user.type(screen.getByLabelText('Name'), 'a')
      expect(handleChange).toHaveBeenCalled()
    })

    it('calls onKeyDown handler', () => {
      const handleKeyDown = vi.fn()
      render(<Input label="Name" onKeyDown={handleKeyDown} />)

      fireEvent.keyDown(screen.getByLabelText('Name'), { key: 'Enter' })
      expect(handleKeyDown).toHaveBeenCalled()
    })

    it('calls onKeyUp handler', () => {
      const handleKeyUp = vi.fn()
      render(<Input label="Name" onKeyUp={handleKeyUp} />)

      fireEvent.keyUp(screen.getByLabelText('Name'), { key: 'Enter' })
      expect(handleKeyUp).toHaveBeenCalled()
    })
  })

  describe('Disabled State', () => {
    it('applies disabled attribute', () => {
      render(<Input disabled label="Name" />)
      expect(screen.getByLabelText('Name')).toBeDisabled()
    })

    it('has disabled styles', () => {
      render(<Input disabled />)
      expect(screen.getByRole('textbox')).toHaveClass('disabled:bg-slate-100')
    })
  })

  describe('Custom className', () => {
    it('applies custom className to input', () => {
      render(<Input className="custom-input" />)
      expect(screen.getByRole('textbox')).toHaveClass('custom-input')
    })
  })

  describe('HTML Attributes', () => {
    it('passes through HTML attributes', () => {
      render(<Input placeholder="Enter text" maxLength={100} />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('placeholder', 'Enter text')
      expect(input).toHaveAttribute('maxLength', '100')
    })

    it('supports ref forwarding', () => {
      const ref = { current: null }
      render(<Input ref={ref} />)
      expect(ref.current).toBeInstanceOf(HTMLInputElement)
    })

    it('uses provided id for label association', () => {
      render(<Input id="my-input" label="My Input" />)
      expect(screen.getByLabelText('My Input')).toHaveAttribute('id', 'my-input')
    })
  })

  describe('Accessibility', () => {
    it('has minimum tap target height', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toHaveClass('min-h-[2.75rem]')
    })

    it('links helper text with aria-describedby', () => {
      render(<Input id="name" helperText="Enter your full name" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-describedby', 'name-helper')
    })

    it('error message has alert role', () => {
      render(<Input error="This field is required" />)
      expect(screen.getByRole('alert')).toHaveTextContent('This field is required')
    })
  })
})
