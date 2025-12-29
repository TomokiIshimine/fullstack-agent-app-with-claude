import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogout } from '@/hooks/useLogout'
import { useVersion } from '@/hooks/useVersion'

interface PageHeaderProps {
  title: string
  user?: { name?: string | null; email: string }
  onBack?: () => void
  showSettings?: boolean
  showLogout?: boolean
}

/**
 * 共通ページヘッダーコンポーネント
 *
 * 全ページで統一されたヘッダーUIを提供します。
 * - タイトル表示
 * - 戻るボタン（オプション）
 * - 右上ハンバーガーメニュー
 *   - バージョン情報
 *   - ユーザー情報（名前優先、なければメール）
 *   - 設定ボタン（オプション）
 *   - ログアウトボタン（オプション）
 */
export function PageHeader({
  title,
  user,
  onBack,
  showSettings = false,
  showLogout = false,
}: PageHeaderProps) {
  const navigate = useNavigate()
  const { handleLogout } = useLogout()
  const { version, isLoading } = useVersion()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // 外部クリックとEscapeキーでメニューを閉じる
  useEffect(() => {
    if (!isMenuOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isMenuOpen])

  const displayName = user?.name || user?.email

  return (
    <div className="flex items-center justify-between mb-8 py-4 gap-4 flex-wrap sm:flex-nowrap">
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 bg-slate-500 text-white border-none rounded text-sm cursor-pointer transition-colors hover:bg-slate-600 order-first sm:order-none"
          aria-label="戻る"
        >
          ← 戻る
        </button>
      )}
      <h1 className="text-2xl font-bold text-slate-800 flex-1 m-0">{title}</h1>
      <div className="relative" ref={menuRef}>
        <button
          type="button"
          className="flex items-center justify-center w-11 h-11 bg-transparent border-none rounded-lg cursor-pointer text-slate-700 transition-colors hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-expanded={isMenuOpen}
          aria-haspopup="menu"
          aria-label="メニューを開く"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        {isMenuOpen && (
          <div
            className="absolute right-0 top-full mt-2 min-w-[200px] bg-white border border-slate-200 rounded-lg shadow-lg z-50 overflow-hidden"
            role="menu"
          >
            <div className="px-4 py-3 border-b border-slate-200">
              {!isLoading && version && (
                <div className="text-xs text-slate-400 mb-1">{version}</div>
              )}
              {displayName && <div className="text-sm text-slate-700 break-all">{displayName}</div>}
            </div>
            {showSettings && (
              <button
                type="button"
                role="menuitem"
                className="block w-full px-4 py-3 text-left text-sm text-slate-700 bg-transparent border-none cursor-pointer transition-colors hover:bg-slate-50"
                onClick={() => {
                  navigate('/settings')
                  setIsMenuOpen(false)
                }}
              >
                設定
              </button>
            )}
            {showLogout && (
              <button
                type="button"
                role="menuitem"
                className="block w-full px-4 py-3 text-left text-sm text-red-600 bg-transparent border-none cursor-pointer transition-colors hover:bg-red-50"
                onClick={() => {
                  handleLogout()
                  setIsMenuOpen(false)
                }}
              >
                ログアウト
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
