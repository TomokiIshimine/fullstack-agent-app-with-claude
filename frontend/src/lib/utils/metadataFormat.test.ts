import { describe, it, expect } from 'vitest'
import {
  buildMetadata,
  formatCost,
  formatResponseTime,
  formatTokens,
  formatModelName,
  type RawMetadataFields,
} from './metadataFormat'

describe('metadataFormat', () => {
  describe('buildMetadata', () => {
    it('returns undefined when all fields are null/undefined', () => {
      const data: RawMetadataFields = {
        input_tokens: null,
        output_tokens: null,
        model: null,
        response_time_ms: null,
        cost_usd: null,
      }
      expect(buildMetadata(data)).toBeUndefined()
    })

    it('returns undefined when data is empty object', () => {
      const data: RawMetadataFields = {}
      expect(buildMetadata(data)).toBeUndefined()
    })

    it('returns metadata when at least one field is present', () => {
      const data: RawMetadataFields = {
        input_tokens: 100,
      }
      const result = buildMetadata(data)
      expect(result).toBeDefined()
      expect(result?.inputTokens).toBe(100)
    })

    it('converts snake_case to camelCase correctly', () => {
      const data: RawMetadataFields = {
        input_tokens: 100,
        output_tokens: 200,
        model: 'claude-3',
        response_time_ms: 1500,
        cost_usd: 0.002,
      }
      const result = buildMetadata(data)

      expect(result).toEqual({
        inputTokens: 100,
        outputTokens: 200,
        model: 'claude-3',
        responseTimeMs: 1500,
        costUsd: 0.002,
      })
    })

    it('converts null values to undefined', () => {
      const data: RawMetadataFields = {
        input_tokens: 100,
        output_tokens: null,
        model: 'claude-3',
        response_time_ms: null,
        cost_usd: null,
      }
      const result = buildMetadata(data)

      expect(result?.inputTokens).toBe(100)
      expect(result?.outputTokens).toBeUndefined()
      expect(result?.model).toBe('claude-3')
      expect(result?.responseTimeMs).toBeUndefined()
      expect(result?.costUsd).toBeUndefined()
    })

    it('returns metadata when only model is present', () => {
      const data: RawMetadataFields = {
        model: 'claude-3',
      }
      const result = buildMetadata(data)
      expect(result).toBeDefined()
      expect(result?.model).toBe('claude-3')
    })
  })

  describe('formatCost', () => {
    it('formats very small costs with 6 decimal places', () => {
      expect(formatCost(0.000001)).toBe('$0.000001')
      expect(formatCost(0.00001)).toBe('$0.000010')
      expect(formatCost(0.00005)).toBe('$0.000050')
    })

    it('formats small costs with 4 decimal places', () => {
      expect(formatCost(0.0001)).toBe('$0.0001')
      expect(formatCost(0.001)).toBe('$0.0010')
      expect(formatCost(0.005)).toBe('$0.0050')
    })

    it('formats regular costs with 2 decimal places', () => {
      expect(formatCost(0.01)).toBe('$0.01')
      expect(formatCost(0.1)).toBe('$0.10')
      expect(formatCost(1.5)).toBe('$1.50')
      expect(formatCost(10)).toBe('$10.00')
    })

    it('handles zero cost', () => {
      expect(formatCost(0)).toBe('$0.000000')
    })

    it('handles boundary values correctly', () => {
      // At threshold (0.0001) - should use 4 decimal places
      expect(formatCost(0.0001)).toBe('$0.0001')
      // Just below threshold - should use 6 decimal places
      expect(formatCost(0.00009999)).toBe('$0.000100')
      // At threshold (0.01) - should use 2 decimal places
      expect(formatCost(0.01)).toBe('$0.01')
      // Just below threshold - should use 4 decimal places
      expect(formatCost(0.0099)).toBe('$0.0099')
    })
  })

  describe('formatResponseTime', () => {
    it('formats times under 1 second in milliseconds', () => {
      expect(formatResponseTime(100)).toBe('100ms')
      expect(formatResponseTime(500)).toBe('500ms')
      expect(formatResponseTime(999)).toBe('999ms')
    })

    it('formats times 1 second and over in seconds', () => {
      expect(formatResponseTime(1000)).toBe('1.0s')
      expect(formatResponseTime(1500)).toBe('1.5s')
      expect(formatResponseTime(2000)).toBe('2.0s')
      expect(formatResponseTime(10000)).toBe('10.0s')
    })

    it('handles zero milliseconds', () => {
      expect(formatResponseTime(0)).toBe('0ms')
    })

    it('handles large values', () => {
      expect(formatResponseTime(60000)).toBe('60.0s')
      expect(formatResponseTime(123456)).toBe('123.5s')
    })
  })

  describe('formatTokens', () => {
    it('formats small numbers without separators', () => {
      expect(formatTokens(100)).toBe('100')
      expect(formatTokens(999)).toBe('999')
    })

    it('formats larger numbers with locale separators', () => {
      // Note: This test assumes en-US locale where comma is the separator
      expect(formatTokens(1000)).toMatch(/1[,.]?000/)
      expect(formatTokens(1234567)).toMatch(/1[,.]?234[,.]?567/)
    })

    it('handles zero', () => {
      expect(formatTokens(0)).toBe('0')
    })
  })

  describe('formatModelName', () => {
    it('removes date suffix from model name', () => {
      expect(formatModelName('claude-sonnet-4-5-20250929')).toBe('claude-sonnet-4-5')
      expect(formatModelName('claude-3-opus-20240229')).toBe('claude-3-opus')
    })

    it('extracts last segment from path', () => {
      expect(formatModelName('anthropic/claude-sonnet-4-5-20250929')).toBe('claude-sonnet-4-5')
      expect(formatModelName('openai/gpt-4-20240101')).toBe('gpt-4')
    })

    it('handles model names without date suffix', () => {
      expect(formatModelName('gpt-4')).toBe('gpt-4')
      expect(formatModelName('claude-instant')).toBe('claude-instant')
    })

    it('handles model names without path', () => {
      expect(formatModelName('claude-3')).toBe('claude-3')
    })

    it('handles empty string', () => {
      expect(formatModelName('')).toBe('')
    })

    it('handles multiple path segments', () => {
      expect(formatModelName('provider/category/claude-3-20240101')).toBe('claude-3')
    })
  })
})
