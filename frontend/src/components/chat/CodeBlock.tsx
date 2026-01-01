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
    return (
      <code className="px-1.5 py-0.5 bg-slate-200 rounded text-[0.875em] font-mono text-danger-600">
        {children}
      </code>
    )
  }

  return (
    <div className="my-3 rounded-lg overflow-hidden bg-[#282c34]">
      <div
        className={`flex items-center px-4 py-2 bg-[#21252b] border-b border-[#3e4451] ${
          language ? 'justify-between' : 'justify-end'
        }`}
      >
        {language && (
          <span className="text-xs font-medium text-[#abb2bf] uppercase">{language}</span>
        )}
        <button
          className="px-2 py-1 bg-[#3e4451] border-none rounded text-xs text-[#abb2bf] cursor-pointer transition-colors duration-200 hover:bg-[#4b5263]"
          onClick={handleCopy}
          aria-label="Copy code"
          type="button"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
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
