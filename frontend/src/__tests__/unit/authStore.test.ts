import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from '../../store/authStore'
import type { User } from '../../api/types'

const TEST_USER: User = {
  id: 'user-001',
  email: 'test@example.com',
  name: 'Test User',
  avatar_url: null,
}

beforeEach(() => {
  useAuthStore.setState({ token: null, user: null })
})

describe('useAuthStore', () => {
  it('starts with null token and user', () => {
    const { result } = renderHook(() => useAuthStore())
    expect(result.current.token).toBeNull()
    expect(result.current.user).toBeNull()
  })

  it('setAuth stores token and user', () => {
    const { result } = renderHook(() => useAuthStore())
    act(() => result.current.setAuth('my-jwt-token', TEST_USER))
    expect(result.current.token).toBe('my-jwt-token')
    expect(result.current.user).toEqual(TEST_USER)
  })

  it('logout clears token and user', () => {
    const { result } = renderHook(() => useAuthStore())
    act(() => result.current.setAuth('token', TEST_USER))
    act(() => result.current.logout())
    expect(result.current.token).toBeNull()
    expect(result.current.user).toBeNull()
  })
})
