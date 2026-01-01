import { useState, useRef, useCallback, useEffect, type KeyboardEvent, type FormEvent } from 'react'

interface ChatInputProps {
  onSend: (message: string) => Promise<void>
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'メッセージを入力...',
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
    }
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [message, adjustHeight])

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || disabled || isSending) return

    setIsSending(true)
    setMessage('')
    try {
      await onSend(trimmed)
    } finally {
      setIsSending(false)
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSubmit()
    }
  }

  const isDisabled = disabled || isSending

  return (
    <div className="px-4 md:px-6 py-4 border-t border-slate-200 bg-white">
      <form className="max-w-3xl mx-auto flex gap-3 items-end" onSubmit={handleSubmit}>
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            className="w-full min-h-11 max-h-40 py-3 px-4 border border-gray-300 rounded-3xl resize-none text-[15px] leading-normal transition-all duration-200 overflow-y-auto focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 disabled:bg-slate-100 disabled:cursor-not-allowed placeholder:text-slate-400 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isDisabled}
            rows={1}
          />
        </div>
        <button
          type="submit"
          className="w-11 h-11 rounded-full bg-primary-500 text-white border-none cursor-pointer flex items-center justify-center transition-colors duration-200 shrink-0 hover:bg-primary-600 disabled:bg-slate-400 disabled:cursor-not-allowed"
          disabled={isDisabled || !message.trim()}
          aria-label="送信"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22L11 13L2 9L22 2Z" />
          </svg>
        </button>
      </form>
    </div>
  )
}
