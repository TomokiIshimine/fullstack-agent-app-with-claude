import { Button } from '@/components/ui'
import type { PaginationMeta } from '@/types/chat'

interface PaginationProps {
  meta: PaginationMeta
  currentPage: number
  onPageChange: (page: number) => void
}

export function Pagination({ meta, currentPage, onPageChange }: PaginationProps) {
  if (meta.total_pages <= 1) {
    return null
  }

  const pages: number[] = []
  const maxVisiblePages = 5
  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
  const endPage = Math.min(meta.total_pages, startPage + maxVisiblePages - 1)

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  return (
    <div className="flex items-center justify-between mt-6">
      <div className="text-sm text-slate-600">
        全 {meta.total} 件中 {(currentPage - 1) * meta.per_page + 1} -{' '}
        {Math.min(currentPage * meta.per_page, meta.total)} 件表示
      </div>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
        >
          前へ
        </Button>
        {startPage > 1 && (
          <>
            <Button size="sm" variant="secondary" onClick={() => onPageChange(1)}>
              1
            </Button>
            {startPage > 2 && <span className="text-slate-400">...</span>}
          </>
        )}
        {pages.map(page => (
          <Button
            key={page}
            size="sm"
            variant={page === currentPage ? 'primary' : 'secondary'}
            onClick={() => onPageChange(page)}
          >
            {page}
          </Button>
        ))}
        {endPage < meta.total_pages && (
          <>
            {endPage < meta.total_pages - 1 && <span className="text-slate-400">...</span>}
            <Button size="sm" variant="secondary" onClick={() => onPageChange(meta.total_pages)}>
              {meta.total_pages}
            </Button>
          </>
        )}
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= meta.total_pages}
        >
          次へ
        </Button>
      </div>
    </div>
  )
}
