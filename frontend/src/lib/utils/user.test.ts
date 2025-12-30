import { describe, it, expect } from 'vitest'
import { getDisplayName, getAvatarLetter } from './user'
import type { User } from '@/types/auth'

describe('user', () => {
  describe('getDisplayName', () => {
    it('returns name when name is provided', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: 'Test User' }
      expect(getDisplayName(user)).toBe('Test User')
    })

    it('returns email when name is null', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: null }
      expect(getDisplayName(user)).toBe('test@example.com')
    })

    it('returns email when name is empty string', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: '' }
      expect(getDisplayName(user)).toBe('test@example.com')
    })
  })

  describe('getAvatarLetter', () => {
    it('returns first letter of name uppercased when name is provided', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: 'Test User' }
      expect(getAvatarLetter(user)).toBe('T')
    })

    it('returns lowercase name initial as uppercase', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: 'john' }
      expect(getAvatarLetter(user)).toBe('J')
    })

    it('returns first letter of email uppercased when name is null', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: null }
      expect(getAvatarLetter(user)).toBe('T')
    })

    it('returns first letter of email uppercased when name is empty string', () => {
      const user: User = { id: 1, email: 'admin@example.com', role: 'user', name: '' }
      expect(getAvatarLetter(user)).toBe('A')
    })

    it('handles Japanese characters in name', () => {
      const user: User = { id: 1, email: 'test@example.com', role: 'user', name: '田中太郎' }
      expect(getAvatarLetter(user)).toBe('田')
    })

    it('handles email starting with number', () => {
      const user: User = { id: 1, email: '123test@example.com', role: 'user', name: null }
      expect(getAvatarLetter(user)).toBe('1')
    })
  })
})
