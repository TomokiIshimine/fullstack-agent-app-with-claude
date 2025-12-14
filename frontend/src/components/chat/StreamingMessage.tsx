interface StreamingMessageProps {
  content: string
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  if (!content) {
    return (
      <div className="streaming-message">
        <div className="message-item__avatar" style={{ backgroundColor: '#10b981' }}>
          AI
        </div>
        <div className="streaming-message__content">
          <div className="loading-dots">
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
            <span className="loading-dots__dot" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="streaming-message">
      <div className="message-item__avatar" style={{ backgroundColor: '#10b981' }}>
        AI
      </div>
      <div className="streaming-message__content">
        {content}
        <span className="streaming-message__cursor" />
      </div>
    </div>
  )
}
