import { useState, useRef, useCallback, useEffect, type KeyboardEvent, type FormEvent } from 'react'
import { cn } from '@/lib/utils/cn'
import { isMac, getModifierKeyLabel } from '@/lib/utils/platform'
import type { SendShortcut } from '@/types/userSettings'

/**
 * Textarea styles organized by category for maintainability
 */
const textareaStyles = {
  base: 'w-full resize-none text-[15px] leading-normal overflow-y-auto',
  size: 'min-h-11 max-h-40 py-3 px-4',
  border: 'border border-gray-300 rounded-3xl',
  transition: 'transition-all duration-200',
  focus: 'focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10',
  disabled: 'disabled:bg-slate-100 disabled:cursor-not-allowed',
  placeholder: 'placeholder:text-slate-400',
  scrollbar: '[scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden',
} as const

/**
 * Submit button styles organized by category
 */
const submitButtonStyles = {
  base: 'w-11 h-11 rounded-full border-none cursor-pointer flex items-center justify-center shrink-0',
  color: 'bg-primary-500 text-white',
  transition: 'transition-colors duration-200',
  hover: 'hover:bg-primary-600',
  disabled: 'disabled:bg-slate-400 disabled:cursor-not-allowed',
} as const

interface ChatInputProps {
  onSend: (message: string) => Promise<void>
  disabled?: boolean
  placeholder?: string
  sendShortcut?: SendShortcut
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'メッセージを入力...',
  sendShortcut = 'enter',
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

    const originalMessage = message
    setIsSending(true)
    setMessage('')
    try {
      await onSend(trimmed)
    } catch {
      // 送信失敗時は入力内容を復元
      setMessage(originalMessage)
    } finally {
      setIsSending(false)
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // IME入力中（日本語変換中など）は送信しない
    if (e.nativeEvent.isComposing) return

    if (sendShortcut === 'enter') {
      // Enter送信モード: Enter で送信、Shift+Enter で改行
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        void handleSubmit()
      }
    } else {
      // Ctrl+Enter送信モード: Ctrl+Enter (macOS: Cmd+Enter) で送信
      const isModifierPressed = isMac() ? e.metaKey : e.ctrlKey
      if (e.key === 'Enter' && isModifierPressed) {
        e.preventDefault()
        void handleSubmit()
      }
      // Enter単押しは改行（デフォルト動作なので何もしない）
    }
  }

  // ヒントテキストの生成
  const modifierKey = getModifierKeyLabel()
  const hintText =
    sendShortcut === 'enter'
      ? 'Enter で送信 / Shift+Enter で改行'
      : `${modifierKey}+Enter で送信 / Enter で改行`

  const isDisabled = disabled || isSending

  return (
    <div className="px-4 md:px-6 py-4 border-t border-slate-200 bg-white">
      <form className="max-w-3xl mx-auto flex gap-3 items-end" onSubmit={handleSubmit}>
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            className={cn(
              textareaStyles.base,
              textareaStyles.size,
              textareaStyles.border,
              textareaStyles.transition,
              textareaStyles.focus,
              textareaStyles.disabled,
              textareaStyles.placeholder,
              textareaStyles.scrollbar
            )}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isDisabled}
            rows={1}
          />
          <p className="mt-1 text-xs text-slate-400">{hintText}</p>
        </div>
        <button
          type="submit"
          className={cn(
            submitButtonStyles.base,
            submitButtonStyles.color,
            submitButtonStyles.transition,
            submitButtonStyles.hover,
            submitButtonStyles.disabled
          )}
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
