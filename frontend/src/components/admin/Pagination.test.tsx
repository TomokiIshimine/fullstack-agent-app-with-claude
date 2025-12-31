import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Pagination } from './Pagination'
import type { PaginationMeta } from '@/types/chat'

describe('Pagination', () => {
  const mockOnPageChange = vi.fn()

  beforeEach(() => {
    mockOnPageChange.mockReset()
  })

  describe('Visibility', () => {
    it('should not render when total_pages is 1', () => {
      const meta: PaginationMeta = { total: 10, page: 1, per_page: 20, total_pages: 1 }
      const { container } = render(
        <Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />
      )

      expect(container.firstChild).toBeNull()
    })

    it('should render when total_pages is greater than 1', () => {
      const meta: PaginationMeta = { total: 50, page: 1, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      expect(screen.getByText('前へ')).toBeInTheDocument()
      expect(screen.getByText('次へ')).toBeInTheDocument()
    })
  })

  describe('Info Display', () => {
    it('should display correct item range on first page', () => {
      const meta: PaginationMeta = { total: 50, page: 1, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      expect(screen.getByText(/全 50 件中 1 - 20 件表示/)).toBeInTheDocument()
    })

    it('should display correct item range on middle page', () => {
      const meta: PaginationMeta = { total: 50, page: 2, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={2} onPageChange={mockOnPageChange} />)

      expect(screen.getByText(/全 50 件中 21 - 40 件表示/)).toBeInTheDocument()
    })

    it('should display correct item range on last page', () => {
      const meta: PaginationMeta = { total: 50, page: 3, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={3} onPageChange={mockOnPageChange} />)

      expect(screen.getByText(/全 50 件中 41 - 50 件表示/)).toBeInTheDocument()
    })
  })

  describe('Navigation Buttons', () => {
    it('should disable previous button on first page', () => {
      const meta: PaginationMeta = { total: 50, page: 1, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      expect(screen.getByRole('button', { name: '前へ' })).toBeDisabled()
    })

    it('should disable next button on last page', () => {
      const meta: PaginationMeta = { total: 50, page: 3, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={3} onPageChange={mockOnPageChange} />)

      expect(screen.getByRole('button', { name: '次へ' })).toBeDisabled()
    })

    it('should enable both buttons on middle page', () => {
      const meta: PaginationMeta = { total: 50, page: 2, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={2} onPageChange={mockOnPageChange} />)

      expect(screen.getByRole('button', { name: '前へ' })).not.toBeDisabled()
      expect(screen.getByRole('button', { name: '次へ' })).not.toBeDisabled()
    })

    it('should call onPageChange with previous page when clicking previous', () => {
      const meta: PaginationMeta = { total: 50, page: 2, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={2} onPageChange={mockOnPageChange} />)

      fireEvent.click(screen.getByRole('button', { name: '前へ' }))

      expect(mockOnPageChange).toHaveBeenCalledWith(1)
    })

    it('should call onPageChange with next page when clicking next', () => {
      const meta: PaginationMeta = { total: 50, page: 2, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={2} onPageChange={mockOnPageChange} />)

      fireEvent.click(screen.getByRole('button', { name: '次へ' }))

      expect(mockOnPageChange).toHaveBeenCalledWith(3)
    })
  })

  describe('Page Numbers', () => {
    it('should display page numbers', () => {
      const meta: PaginationMeta = { total: 50, page: 1, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument()
    })

    it('should call onPageChange when clicking page number', () => {
      const meta: PaginationMeta = { total: 50, page: 1, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      fireEvent.click(screen.getByRole('button', { name: '2' }))

      expect(mockOnPageChange).toHaveBeenCalledWith(2)
    })

    it('should highlight current page', () => {
      const meta: PaginationMeta = { total: 50, page: 2, per_page: 20, total_pages: 3 }
      render(<Pagination meta={meta} currentPage={2} onPageChange={mockOnPageChange} />)

      const currentPageButton = screen.getByRole('button', { name: '2' })
      // Check for primary variant styling
      expect(currentPageButton).toHaveClass('bg-blue-500')
    })
  })

  describe('Ellipsis Display', () => {
    it('should show ellipsis for many pages', () => {
      const meta: PaginationMeta = { total: 200, page: 5, per_page: 20, total_pages: 10 }
      render(<Pagination meta={meta} currentPage={5} onPageChange={mockOnPageChange} />)

      // Should show first page, ellipsis, visible pages, ellipsis, last page
      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: '10' })).toBeInTheDocument()
      expect(screen.getAllByText('...')).toHaveLength(2)
    })

    it('should not show start ellipsis when at beginning', () => {
      const meta: PaginationMeta = { total: 200, page: 1, per_page: 20, total_pages: 10 }
      render(<Pagination meta={meta} currentPage={1} onPageChange={mockOnPageChange} />)

      // Should only show end ellipsis
      expect(screen.getAllByText('...')).toHaveLength(1)
      expect(screen.getByRole('button', { name: '10' })).toBeInTheDocument()
    })

    it('should not show end ellipsis when at end', () => {
      const meta: PaginationMeta = { total: 200, page: 10, per_page: 20, total_pages: 10 }
      render(<Pagination meta={meta} currentPage={10} onPageChange={mockOnPageChange} />)

      // Should only show start ellipsis
      expect(screen.getAllByText('...')).toHaveLength(1)
      expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument()
    })
  })

  describe('First and Last Page Quick Access', () => {
    it('should navigate to first page when clicking first page button', () => {
      const meta: PaginationMeta = { total: 200, page: 5, per_page: 20, total_pages: 10 }
      render(<Pagination meta={meta} currentPage={5} onPageChange={mockOnPageChange} />)

      fireEvent.click(screen.getByRole('button', { name: '1' }))

      expect(mockOnPageChange).toHaveBeenCalledWith(1)
    })

    it('should navigate to last page when clicking last page button', () => {
      const meta: PaginationMeta = { total: 200, page: 5, per_page: 20, total_pages: 10 }
      render(<Pagination meta={meta} currentPage={5} onPageChange={mockOnPageChange} />)

      fireEvent.click(screen.getByRole('button', { name: '10' }))

      expect(mockOnPageChange).toHaveBeenCalledWith(10)
    })
  })
})
