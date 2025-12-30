import type { AdminConversation } from '@/types/adminConversation'
import { Button } from '@/components/ui'

interface ConversationListProps {
  conversations: AdminConversation[]
  onViewDetail: (uuid: string) => void
}

export function ConversationList({ conversations, onViewDetail }: ConversationListProps) {
  if (conversations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-md p-8 text-center">
        <p className="text-slate-600">会話履歴がありません</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                タイトル
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                ユーザー
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                メッセージ数
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                作成日
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                最終更新
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-700 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {conversations.map(conversation => (
              <tr key={conversation.uuid} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 max-w-xs truncate">
                  {conversation.title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                  <div>{conversation.user.name || '-'}</div>
                  <div className="text-slate-500 text-xs">{conversation.user.email}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {conversation.messageCount}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {conversation.createdAt.toLocaleDateString('ja-JP')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {conversation.updatedAt.toLocaleDateString('ja-JP')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Button size="sm" onClick={() => onViewDetail(conversation.uuid)}>
                    詳細
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
