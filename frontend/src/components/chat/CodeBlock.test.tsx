import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CodeBlock } from './CodeBlock'

describe('CodeBlock', () => {
  describe('Inline Code', () => {
    it('renders inline code with correct class', () => {
      render(<CodeBlock inline>const x = 1</CodeBlock>)
      const code = screen.getByText('const x = 1')
      expect(code).toHaveClass('markdown-inline-code')
      expect(code.tagName).toBe('CODE')
    })

    it('does not render copy button for inline code', () => {
      render(<CodeBlock inline>const x = 1</CodeBlock>)
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Code Blocks', () => {
    it('renders code block with syntax highlighting', () => {
      render(<CodeBlock language="javascript">const x = 1;</CodeBlock>)
      expect(screen.getByText(/const/)).toBeInTheDocument()
    })

    it('displays language label when provided', () => {
      render(<CodeBlock language="python">print("hello")</CodeBlock>)
      expect(screen.getByText('python')).toBeInTheDocument()
    })

    it('renders copy button with language', () => {
      render(<CodeBlock language="javascript">const x = 1;</CodeBlock>)
      expect(screen.getByRole('button', { name: 'Copy code' })).toBeInTheDocument()
    })

    it('renders copy button without language', () => {
      render(<CodeBlock>plain text</CodeBlock>)
      expect(screen.getByRole('button', { name: 'Copy code' })).toBeInTheDocument()
    })

    it('calls clipboard API when copy button clicked', async () => {
      const user = userEvent.setup()
      const writeTextSpy = vi
        .spyOn(navigator.clipboard, 'writeText')
        .mockResolvedValue(undefined)

      render(<CodeBlock language="javascript">const x = 1;</CodeBlock>)

      await user.click(screen.getByRole('button', { name: 'Copy code' }))

      expect(writeTextSpy).toHaveBeenCalledWith('const x = 1;')
      writeTextSpy.mockRestore()
    })

    it('shows Copied! text after clicking copy', async () => {
      const user = userEvent.setup()
      render(<CodeBlock language="javascript">const x = 1;</CodeBlock>)

      await user.click(screen.getByRole('button', { name: 'Copy code' }))

      expect(screen.getByText('Copied!')).toBeInTheDocument()
    })

    it('trims trailing newlines from code', () => {
      render(<CodeBlock language="javascript">{'const x = 1;\n\n'}</CodeBlock>)
      expect(screen.getByText(/const/)).toBeInTheDocument()
    })
  })

  describe('Language Support', () => {
    const languages = ['javascript', 'python', 'typescript', 'bash', 'json']

    languages.forEach(lang => {
      it(`renders ${lang} code block with language label`, () => {
        render(<CodeBlock language={lang}>code here</CodeBlock>)
        expect(screen.getByText(lang)).toBeInTheDocument()
      })
    })
  })
})
