import { memo, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'
import type { Components } from 'react-markdown'
import { CodeBlock } from './CodeBlock'

interface MarkdownRendererProps {
  content: string
  className?: string
  isUserMessage?: boolean
}

function createMarkdownComponents(isUserMessage: boolean): Components {
  return {
    code({ className, children, ...rest }) {
      const match = /language-(\w+)/.exec(className || '')
      const language = match ? match[1] : undefined
      const codeString = String(children).replace(/\n$/, '')

      // Check if this is inline code (no language and single line)
      // Code blocks are wrapped in <pre> and have language or multiple lines
      const isInline = !language && !codeString.includes('\n')

      if (isInline) {
        return (
          <code
            className={`px-1.5 py-0.5 rounded text-[0.875em] font-mono ${
              isUserMessage
                ? 'bg-white/20 text-white'
                : 'bg-slate-200 text-danger-600'
            }`}
            {...rest}
          >
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
          className={`underline underline-offset-2 ${
            isUserMessage
              ? 'text-primary-200 hover:text-white'
              : 'text-primary-500 hover:text-primary-600'
          }`}
        >
          {children}
        </a>
      )
    },

    table({ children }) {
      return (
        <div className="my-3 overflow-x-auto">
          <table className="w-full border-collapse text-sm">{children}</table>
        </div>
      )
    },

    th({ children }) {
      return (
        <th
          className={`px-3 py-2 border text-left font-semibold ${
            isUserMessage
              ? 'border-white/30 bg-white/10'
              : 'border-slate-200 bg-slate-50'
          }`}
        >
          {children}
        </th>
      )
    },

    td({ children }) {
      return (
        <td
          className={`px-3 py-2 border ${
            isUserMessage ? 'border-white/30' : 'border-slate-200'
          }`}
        >
          {children}
        </td>
      )
    },

    blockquote({ children }) {
      return (
        <blockquote
          className={`my-3 py-2 px-4 border-l-4 ${
            isUserMessage
              ? 'bg-white/10 border-white/50 text-white'
              : 'bg-slate-100 border-primary-500 text-slate-600'
          }`}
        >
          {children}
        </blockquote>
      )
    },

    pre({ children }) {
      return <>{children}</>
    },
  }
}

export const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  className = '',
  isUserMessage = false,
}: MarkdownRendererProps) {
  const components = useMemo(() => createMarkdownComponents(isUserMessage), [isUserMessage])

  if (!content) return null

  return (
    <div
      className={`whitespace-normal prose prose-sm max-w-none prose-headings:font-semibold prose-headings:leading-tight prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:my-3 first:prose-p:mt-0 last:prose-p:mb-0 prose-ul:my-3 prose-ul:pl-6 prose-ol:my-3 prose-ol:pl-6 prose-li:my-1 prose-strong:font-semibold prose-em:italic prose-hr:my-6 prose-hr:border-slate-200 prose-img:max-w-full prose-img:rounded-lg prose-img:my-3 ${className}`}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
})
