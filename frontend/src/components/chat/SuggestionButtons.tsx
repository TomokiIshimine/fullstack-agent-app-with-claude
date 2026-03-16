import type React from 'react'

interface SuggestionButtonsProps {
  suggestions: string[]
  isLoading: boolean
  onSelect: (suggestion: string) => void
}

export const SuggestionButtons: React.FC<SuggestionButtonsProps> = ({
  suggestions,
  isLoading,
  onSelect,
}) => {
  if (!isLoading && suggestions.length === 0) {
    return null
  }

  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-2" data-testid="suggestion-skeleton">
        {[1, 2, 3].map(i => (
          <div
            key={i}
            className="h-9 w-32 animate-pulse rounded-full bg-slate-200"
            role="status"
            aria-label="選択肢を読み込み中"
          />
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-2 animate-fadeIn">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          type="button"
          className="max-w-full break-words border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 hover:border-primary-400 hover:text-primary-600 rounded-full px-4 py-2 text-sm transition-colors"
          onClick={() => onSelect(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}
