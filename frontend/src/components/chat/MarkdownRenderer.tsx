import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import { CodeBlock } from './CodeBlock'

interface MarkdownRendererProps {
  content: string
  className?: string
}

const markdownComponents: Components = {
  code({ className, children, ...rest }) {
    const match = /language-(\w+)/.exec(className || '')
    const language = match ? match[1] : undefined
    const codeString = String(children).replace(/\n$/, '')

    // Check if this is inline code (no language and single line)
    // Code blocks are wrapped in <pre> and have language or multiple lines
    const isInline = !language && !codeString.includes('\n')

    if (isInline) {
      return (
        <code className="markdown-inline-code" {...rest}>
          {children}
        </code>
      )
    }

    return <CodeBlock language={language}>{codeString}</CodeBlock>
  },

  a({ href, children }) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="markdown-link"
      >
        {children}
      </a>
    )
  },

  table({ children }) {
    return (
      <div className="markdown-table-wrapper">
        <table className="markdown-table">{children}</table>
      </div>
    )
  },

  pre({ children }) {
    return <>{children}</>
  },
}

export const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  className = '',
}: MarkdownRendererProps) {
  if (!content) return null

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  )
})
