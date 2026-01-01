import { Modal, Button } from '@/components/ui'
import { cn } from '@/lib/utils/cn'
import type { MessageDto } from '@/types/chat'

interface ConversationDetail {
  uuid: string
  title: string
  user: {
    id: number
    email: string
    name: string | null
  }
  messages: MessageDto[]
  createdAt: Date
  updatedAt: Date
}

interface ConversationDetailModalProps {
  conversation: ConversationDetail | null
  isLoading: boolean
  onClose: () => void
}

export function ConversationDetailModal({
  conversation,
  isLoading,
  onClose,
}: ConversationDetailModalProps) {
  if (!conversation && !isLoading) {
    return null
  }

  return (
    <Modal isOpen={conversation !== null || isLoading} onClose={onClose} title="会話詳細" size="lg">
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-slate-600">読み込み中...</div>
        </div>
      ) : conversation ? (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <h4 className="font-semibold text-slate-800 mb-2">{conversation.title}</h4>
            <div className="text-sm text-slate-600 space-y-1">
              <p>
                <span className="font-medium">ユーザー:</span>{' '}
                {conversation.user.name || conversation.user.email}
              </p>
              <p>
                <span className="font-medium">メールアドレス:</span> {conversation.user.email}
              </p>
              <p>
                <span className="font-medium">作成日:</span>{' '}
                {conversation.createdAt.toLocaleString('ja-JP')}
              </p>
              <p>
                <span className="font-medium">最終更新:</span>{' '}
                {conversation.updatedAt.toLocaleString('ja-JP')}
              </p>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <h5 className="font-semibold text-slate-700 mb-3">
              メッセージ ({conversation.messages.length}件)
            </h5>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {conversation.messages.map(message => (
                <div
                  key={message.id}
                  className={cn(
                    'p-3 rounded-lg',
                    message.role === 'user' ? 'bg-blue-50 ml-4' : 'bg-slate-100 mr-4'
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={cn(
                        'text-xs font-semibold px-2 py-0.5 rounded',
                        message.role === 'user'
                          ? 'bg-blue-200 text-blue-800'
                          : 'bg-slate-300 text-slate-800'
                      )}
                    >
                      {message.role === 'user' ? 'ユーザー' : 'アシスタント'}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(message.created_at).toLocaleString('ja-JP')}
                    </span>
                  </div>
                  <p className="text-sm text-slate-800 whitespace-pre-wrap">{message.content}</p>
                  {message.role === 'assistant' && message.model && (
                    <div className="mt-2 text-xs text-slate-500">
                      モデル: {message.model}
                      {message.input_tokens && message.output_tokens && (
                        <span className="ml-2">
                          (入力: {message.input_tokens}, 出力: {message.output_tokens} トークン)
                        </span>
                      )}
                      {message.cost_usd && (
                        <span className="ml-2">コスト: ${message.cost_usd.toFixed(6)}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-200">
            <Button onClick={onClose}>閉じる</Button>
          </div>
        </div>
      ) : null}
    </Modal>
  )
}
