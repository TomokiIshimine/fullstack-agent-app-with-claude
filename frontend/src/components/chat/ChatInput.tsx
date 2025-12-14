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
    <div className="chat-input">
      <form className="chat-input__form" onSubmit={handleSubmit}>
        <div className="chat-input__textarea-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input__textarea"
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
          className="chat-input__submit"
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
