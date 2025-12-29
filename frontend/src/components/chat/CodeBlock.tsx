import { useState, useCallback } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface CodeBlockProps {
  language?: string
  children: string
  inline?: boolean
}

export function CodeBlock({ language, children, inline = false }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(children)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy code:', err)
    }
  }, [children])

  if (inline) {
    return <code className="markdown-inline-code">{children}</code>
  }

  return (
    <div className="markdown-code-block">
      {language && (
        <div className="markdown-code-block__header">
          <span className="markdown-code-block__language">{language}</span>
          <button
            className="markdown-code-block__copy"
            onClick={handleCopy}
            aria-label="Copy code"
            type="button"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      )}
      {!language && (
        <div className="markdown-code-block__header markdown-code-block__header--copy-only">
          <button
            className="markdown-code-block__copy"
            onClick={handleCopy}
            aria-label="Copy code"
            type="button"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      )}
      <SyntaxHighlighter
        language={language || 'text'}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: '1rem',
          borderRadius: '0 0 0.5rem 0.5rem',
          fontSize: '0.875rem',
        }}
        PreTag="div"
      >
        {children.trim()}
      </SyntaxHighlighter>
    </div>
  )
}
