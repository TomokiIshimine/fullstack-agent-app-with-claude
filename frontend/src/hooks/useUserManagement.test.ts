import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useUserManagement } from './useUserManagement'

// Mock the API module
vi.mock('@/lib/api/users', () => ({
  fetchUsers: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
}))

// Mock logger
vi.mock('@/lib/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

import { fetchUsers, createUser, deleteUser } from '@/lib/api/users'
import type { UserResponse, UserCreateResponse } from '@/types/user'

const mockUsers: UserResponse[] = [
  {
    id: 1,
    email: 'admin@example.com',
    name: 'Admin User',
    role: 'admin',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    email: 'user@example.com',
    name: 'Regular User',
    role: 'user',
    created_at: '2025-01-02T00:00:00Z',
  },
]

const mockCreateResponse: UserCreateResponse = {
  user: {
    id: 3,
    email: 'newuser@example.com',
    name: 'New User',
    role: 'user',
    created_at: '2025-01-03T00:00:00Z',
  },
  initial_password: 'test123456ab',
}

describe('useUserManagement', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetchUsers).mockResolvedValue(mockUsers)
    vi.mocked(createUser).mockResolvedValue(mockCreateResponse)
    vi.mocked(deleteUser).mockResolvedValue()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial state and auto-load', () => {
    it('should auto-load users on mount', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(fetchUsers).toHaveBeenCalled()
      expect(result.current.users).toHaveLength(2)
      expect(result.current.users[0].email).toBe('admin@example.com')
    })

    it('should have correct initial state', async () => {
      const { result } = renderHook(() => useUserManagement())

      // Initially loading
      expect(result.current.isLoading).toBe(true)
      expect(result.current.error).toBeNull()
      expect(result.current.initialPassword).toBeNull()

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('loadUsers', () => {
    it('should load users successfully', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.users).toEqual(mockUsers)
    })

    it('should handle error when loading users', async () => {
      vi.mocked(fetchUsers).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBe('Network error')
      expect(result.current.users).toEqual([])
    })

    it('should clear error before loading', async () => {
      vi.mocked(fetchUsers)
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(mockUsers)

      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.error).toBe('First error')
      })

      // Reload
      await act(async () => {
        await result.current.loadUsers()
      })

      expect(result.current.error).toBeNull()
      expect(result.current.users).toEqual(mockUsers)
    })
  })

  describe('createUser', () => {
    it('should create user successfully and set initial password', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let response: UserCreateResponse | undefined
      await act(async () => {
        response = await result.current.createUser({
          email: 'newuser@example.com',
          name: 'New User',
        })
      })

      expect(createUser).toHaveBeenCalledWith({
        email: 'newuser@example.com',
        name: 'New User',
      })
      expect(response).toEqual(mockCreateResponse)
      expect(result.current.initialPassword).toEqual({
        email: 'newuser@example.com',
        password: 'test123456ab',
      })
    })

    it('should reload users after creating', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      vi.mocked(fetchUsers).mockClear()

      await act(async () => {
        await result.current.createUser({
          email: 'newuser@example.com',
          name: 'New User',
        })
      })

      expect(fetchUsers).toHaveBeenCalled()
    })

    it('should handle error when creating user', async () => {
      vi.mocked(createUser).mockRejectedValue(new Error('Email already exists'))

      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let caughtError: Error | undefined
      await act(async () => {
        try {
          await result.current.createUser({
            email: 'existing@example.com',
            name: 'Existing User',
          })
        } catch (err) {
          caughtError = err as Error
        }
      })

      expect(caughtError?.message).toBe('Email already exists')
      expect(result.current.error).toBe('Email already exists')
      expect(result.current.initialPassword).toBeNull()
    })
  })

  describe('deleteUser', () => {
    it('should delete user successfully', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const userToDelete = mockUsers[1]

      await act(async () => {
        await result.current.deleteUser(userToDelete)
      })

      expect(deleteUser).toHaveBeenCalledWith(userToDelete.id)
    })

    it('should reload users after deleting', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      vi.mocked(fetchUsers).mockClear()

      await act(async () => {
        await result.current.deleteUser(mockUsers[1])
      })

      expect(fetchUsers).toHaveBeenCalled()
    })

    it('should handle error when deleting user', async () => {
      vi.mocked(deleteUser).mockRejectedValue(new Error('Cannot delete admin'))

      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      let caughtError: Error | undefined
      await act(async () => {
        try {
          await result.current.deleteUser(mockUsers[0])
        } catch (err) {
          caughtError = err as Error
        }
      })

      expect(caughtError?.message).toBe('Cannot delete admin')
      expect(result.current.error).toBe('Cannot delete admin')
    })
  })

  describe('resetInitialPassword', () => {
    it('should reset initial password state', async () => {
      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // First create a user to set initial password
      await act(async () => {
        await result.current.createUser({
          email: 'newuser@example.com',
          name: 'New User',
        })
      })

      expect(result.current.initialPassword).not.toBeNull()

      // Then reset it
      act(() => {
        result.current.resetInitialPassword()
      })

      expect(result.current.initialPassword).toBeNull()
    })
  })

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(fetchUsers).mockRejectedValue(new Error('Error'))

      const { result } = renderHook(() => useUserManagement())

      await waitFor(() => {
        expect(result.current.error).toBe('Error')
      })

      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })
  })
})
