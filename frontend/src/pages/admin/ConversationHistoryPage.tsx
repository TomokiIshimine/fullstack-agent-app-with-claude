import { Alert } from '@/components/ui'
import { ConversationFilters } from '@/components/admin/ConversationFilters'
import { ConversationList } from '@/components/admin/ConversationList'
import { ConversationDetailModal } from '@/components/admin/ConversationDetailModal'
import { Pagination } from '@/components/admin/Pagination'
import { useAdminConversations } from '@/hooks/useAdminConversations'

export function ConversationHistoryPage() {
  const {
    conversations,
    users,
    pagination,
    isLoading,
    isLoadingDetail,
    selectedConversation,
    filters,
    currentPage,
    error,
    clearError,
    loadConversations,
    loadConversationDetail,
    applyFilters,
    clearFilters,
    goToPage,
    closeDetail,
  } = useAdminConversations()

  return (
    <div className="bg-slate-100 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">会話履歴管理</h1>

        {error && (
          <div className="mb-6">
            <Alert
              variant="error"
              onRetry={() => {
                clearError()
                void loadConversations()
              }}
              onDismiss={clearError}
            >
              {error}
            </Alert>
          </div>
        )}

        <ConversationFilters
          users={users}
          filters={filters}
          onApplyFilters={applyFilters}
          onClearFilters={clearFilters}
        />

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-slate-600 text-lg">読み込み中...</div>
          </div>
        ) : (
          <>
            <ConversationList conversations={conversations} onViewDetail={loadConversationDetail} />
            {pagination && (
              <Pagination meta={pagination} currentPage={currentPage} onPageChange={goToPage} />
            )}
          </>
        )}

        <ConversationDetailModal
          conversation={selectedConversation}
          isLoading={isLoadingDetail}
          onClose={closeDetail}
        />
      </div>
    </div>
  )
}
