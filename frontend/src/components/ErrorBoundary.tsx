import { Component, type ErrorInfo, type ReactNode } from 'react'
import { logger } from '@/lib/logger'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Error Boundary component to catch React component errors
 *
 * Catches errors during rendering, in lifecycle methods, and in constructors
 * of the whole tree below them. Logs errors and displays fallback UI.
 *
 * @example
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    logger.error('React component error', error, {
      componentStack: errorInfo.componentStack,
      type: 'react-error-boundary',
    })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="p-8 max-w-xl mx-auto my-8 border border-danger-500 rounded-lg bg-danger-50">
          <h1 className="text-danger-600 mb-4 text-xl font-bold">エラーが発生しました</h1>
          <p className="mb-4 text-slate-700">
            申し訳ございません。予期しないエラーが発生しました。
          </p>
          {this.state.error && (
            <details className="mb-4">
              <summary className="cursor-pointer font-bold mb-2 text-slate-800">
                エラーの詳細
              </summary>
              <pre className="bg-slate-100 p-4 rounded overflow-auto text-sm text-slate-700">
                {this.state.error.message}
                {'\n\n'}
                {this.state.error.stack}
              </pre>
            </details>
          )}
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null })
              window.location.reload()
            }}
            className="px-4 py-2 bg-primary-500 text-white rounded hover:bg-primary-600 transition-colors cursor-pointer text-base"
          >
            ページを再読み込み
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
