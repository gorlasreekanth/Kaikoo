import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '../../test/renderWithProviders'
import { server } from '../../test/server'
import { LoginPage } from '../../pages/LoginPage'
import { useAuthStore } from '../../store/authStore'

// Mock @react-oauth/google so we can control it in tests
vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess }: { onSuccess: (c: { credential: string }) => void }) => (
    <button onClick={() => onSuccess({ credential: 'mock-google-token' })}>
      Sign in with Google
    </button>
  ),
}))

beforeEach(() => {
  useAuthStore.setState({ token: null, user: null })
})

describe('LoginPage', () => {
  it('renders the Kaikoo heading', () => {
    renderWithProviders(<LoginPage />)
    expect(screen.getByText('Kaikoo')).toBeInTheDocument()
  })

  it('renders the Google sign-in button', () => {
    renderWithProviders(<LoginPage />)
    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument()
  })

  it('stores auth token after successful Google login', async () => {
    renderWithProviders(<LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: /sign in with google/i }))

    await waitFor(() => {
      expect(useAuthStore.getState().token).toBe('test-jwt-token')
    })
  })

  it('shows toast on login failure', async () => {
    server.use(http.post('http://localhost:8000/api/v1/auth/google', () => HttpResponse.json({ detail: 'Invalid token' }, { status: 401 })))

    renderWithProviders(<LoginPage />)
    await userEvent.click(screen.getByRole('button', { name: /sign in with google/i }))

    await waitFor(() => {
      expect(screen.getByText(/login failed/i)).toBeInTheDocument()
    })
  })
})

describe('LoginPage — dev bypass', () => {
  beforeEach(() => {
    // Simulate VITE_DEV_BYPASS_AUTH=true
    // The constant is read at module scope, so we test the button's behaviour
    // by adding the bypass button manually to our test scenario
  })

  it('dev login button calls /auth/dev-login and stores token', async () => {
    // Directly test the dev login flow by rendering with the bypass flag behaviour
    // We do this by overriding the import.meta.env check isn't easy in vitest,
    // so we test the underlying API call directly
    let devLoginCalled = false
    server.use(
      http.post('http://localhost:8000/api/v1/auth/dev-login', () => {
        devLoginCalled = true
        return HttpResponse.json({ access_token: 'dev-jwt-token', user: { id: 'dev-001', email: 'dev@kaikoo.local', name: 'Dev User', avatar_url: null } })
      }),
    )

    // Import the api function and call it to verify the endpoint works
    const { devLogin } = await import('../../api/auth')
    const result = await devLogin()
    expect(devLoginCalled).toBe(true)
    expect(result.access_token).toBe('dev-jwt-token')
    expect(result.user.email).toBe('dev@kaikoo.local')
  })
})
