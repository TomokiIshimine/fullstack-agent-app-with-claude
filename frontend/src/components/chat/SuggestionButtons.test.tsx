import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SuggestionButtons } from './SuggestionButtons'

describe('SuggestionButtons', () => {
  const mockOnSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render nothing when suggestions are empty and not loading', () => {
      const { container } = render(
        <SuggestionButtons suggestions={[]} isLoading={false} onSelect={mockOnSelect} />
      )

      expect(container.innerHTML).toBe('')
    })

    it('should render suggestion buttons', () => {
      const suggestions = ['選択肢1', '選択肢2', '選択肢3']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      expect(screen.getByText('選択肢1')).toBeInTheDocument()
      expect(screen.getByText('選択肢2')).toBeInTheDocument()
      expect(screen.getByText('選択肢3')).toBeInTheDocument()
    })

    it('should render skeleton buttons when loading', () => {
      render(<SuggestionButtons suggestions={[]} isLoading={true} onSelect={mockOnSelect} />)

      expect(screen.getByTestId('suggestion-skeleton')).toBeInTheDocument()
      const skeletons = screen.getAllByRole('status')
      expect(skeletons).toHaveLength(3)
    })

    it('should render skeleton buttons even when suggestions exist during loading', () => {
      render(
        <SuggestionButtons suggestions={['選択肢1']} isLoading={true} onSelect={mockOnSelect} />
      )

      expect(screen.getByTestId('suggestion-skeleton')).toBeInTheDocument()
      expect(screen.queryByText('選択肢1')).not.toBeInTheDocument()
    })
  })

  describe('Interaction', () => {
    it('should call onSelect with suggestion text when clicked', () => {
      const suggestions = ['選択肢A', '選択肢B']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      fireEvent.click(screen.getByText('選択肢A'))

      expect(mockOnSelect).toHaveBeenCalledTimes(1)
      expect(mockOnSelect).toHaveBeenCalledWith('選択肢A')
    })

    it('should call onSelect with the correct suggestion for each button', () => {
      const suggestions = ['選択肢X', '選択肢Y', '選択肢Z']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      fireEvent.click(screen.getByText('選択肢Z'))

      expect(mockOnSelect).toHaveBeenCalledWith('選択肢Z')
    })
  })

  describe('Styling', () => {
    it('should have fadeIn animation class on container', () => {
      const suggestions = ['選択肢1']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      const container = screen.getByText('選択肢1').parentElement
      expect(container?.className).toContain('animate-fadeIn')
    })

    it('should have flex-wrap layout', () => {
      const suggestions = ['選択肢1']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      const container = screen.getByText('選択肢1').parentElement
      expect(container?.className).toContain('flex')
      expect(container?.className).toContain('flex-wrap')
    })

    it('should have rounded-full style on buttons', () => {
      const suggestions = ['選択肢1']

      render(
        <SuggestionButtons suggestions={suggestions} isLoading={false} onSelect={mockOnSelect} />
      )

      const button = screen.getByText('選択肢1')
      expect(button.className).toContain('rounded-full')
    })
  })
})
