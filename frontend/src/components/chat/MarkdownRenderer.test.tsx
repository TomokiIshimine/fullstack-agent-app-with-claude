import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MarkdownRenderer } from './MarkdownRenderer'

describe('MarkdownRenderer', () => {
  describe('Basic Markdown', () => {
    it('renders plain text', () => {
      render(<MarkdownRenderer content="Hello world" />)
      expect(screen.getByText('Hello world')).toBeInTheDocument()
    })

    it('renders headings correctly', () => {
      render(<MarkdownRenderer content="# Heading 1" />)
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Heading 1')
    })

    it('renders h2 heading', () => {
      render(<MarkdownRenderer content="## Heading 2" />)
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Heading 2')
    })

    it('renders bold text', () => {
      render(<MarkdownRenderer content="This is **bold** text" />)
      const strongElement = screen.getByText('bold')
      expect(strongElement.tagName).toBe('STRONG')
    })

    it('renders italic text', () => {
      render(<MarkdownRenderer content="This is *italic* text" />)
      const emElement = screen.getByText('italic')
      expect(emElement.tagName).toBe('EM')
    })

    it('renders unordered lists', () => {
      const content = `- Item 1
- Item 2
- Item 3`
      render(<MarkdownRenderer content={content} />)
      const listItems = screen.getAllByRole('listitem')
      expect(listItems).toHaveLength(3)
    })

    it('renders ordered lists', () => {
      const content = `1. First
2. Second
3. Third`
      render(<MarkdownRenderer content={content} />)
      const list = screen.getByRole('list')
      expect(list.tagName).toBe('OL')
    })
  })

  describe('Code Rendering', () => {
    it('renders inline code with markdown-inline-code class', () => {
      render(<MarkdownRenderer content="Use `const` for constants" />)
      const codeElement = screen.getByText('const')
      expect(codeElement).toHaveClass('markdown-inline-code')
    })

    it('renders code blocks with language', () => {
      const content = `\`\`\`javascript
const x = 1;
\`\`\``
      render(<MarkdownRenderer content={content} />)
      expect(screen.getByText('javascript')).toBeInTheDocument()
    })

    it('renders code blocks without language', () => {
      const content = `\`\`\`
plain text code
\`\`\``
      render(<MarkdownRenderer content={content} />)
      expect(screen.getByText('plain text code')).toBeInTheDocument()
    })
  })

  describe('Links', () => {
    it('renders links with correct attributes', () => {
      render(<MarkdownRenderer content="[Click here](https://example.com)" />)
      const link = screen.getByRole('link', { name: 'Click here' })
      expect(link).toHaveAttribute('href', 'https://example.com')
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })

    it('renders links with markdown-link class', () => {
      render(<MarkdownRenderer content="[Link](https://example.com)" />)
      const link = screen.getByRole('link')
      expect(link).toHaveClass('markdown-link')
    })
  })

  describe('GFM Features', () => {
    it('renders tables', () => {
      const content = `| Header 1 | Header 2 |
|----------|----------|
| Cell 1 | Cell 2 |`
      render(<MarkdownRenderer content={content} />)
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByText('Header 1')).toBeInTheDocument()
    })

    it('renders strikethrough text', () => {
      render(<MarkdownRenderer content="This is ~~deleted~~ text" />)
      const delElement = screen.getByText('deleted')
      expect(delElement.tagName).toBe('DEL')
    })

    it('renders task lists', () => {
      const content = `- [x] Completed
- [ ] Pending`
      render(<MarkdownRenderer content={content} />)
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes).toHaveLength(2)
      expect(checkboxes[0]).toBeChecked()
      expect(checkboxes[1]).not.toBeChecked()
    })
  })

  describe('Blockquotes', () => {
    it('renders blockquotes', () => {
      render(<MarkdownRenderer content="> This is a quote" />)
      const blockquote = screen.getByText('This is a quote').closest('blockquote')
      expect(blockquote).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty content', () => {
      const { container } = render(<MarkdownRenderer content="" />)
      expect(container).toBeEmptyDOMElement()
    })

    it('applies custom className', () => {
      const { container } = render(
        <MarkdownRenderer content="Test" className="custom-class" />
      )
      expect(container.firstChild).toHaveClass('markdown-content', 'custom-class')
    })

    it('handles content with multiple paragraphs', () => {
      const content = `Paragraph 1

Paragraph 2`
      render(<MarkdownRenderer content={content} />)
      expect(screen.getByText('Paragraph 1')).toBeInTheDocument()
      expect(screen.getByText('Paragraph 2')).toBeInTheDocument()
    })
  })
})
