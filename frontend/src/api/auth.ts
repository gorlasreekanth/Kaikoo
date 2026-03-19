import { apiClient } from './client'
import type { User } from './types'

export async function loginWithGoogle(idToken: string): Promise<{ access_token: string; user: User }> {
  const { data } = await apiClient.post('/auth/google', { id_token: idToken })
  return data
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get('/auth/me')
  return data
}

export async function devLogin(): Promise<{ access_token: string; user: User }> {
  const { data } = await apiClient.post('/auth/dev-login')
  return data
}
