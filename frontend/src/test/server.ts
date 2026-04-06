/**
 * MSW mock server — intercepts all /api/v1/* calls during tests.
 */
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import type { User, Category, Note, PaginatedNotes, NoteCreateResponse, IntegrationStatus } from '../api/types'

export const TEST_USER: User = {
  id: 'user-test-001',
  email: 'test@kaikoo.local',
  name: 'Test User',
  avatar_url: null,
}

export const TEST_CATEGORY: Category = {
  id: 'cat-001',
  name: 'Work',
  color: '#7c6af7',
  note_count: 1,
  created_at: '2026-04-06T10:00:00Z',
}

export const TEST_NOTE: Note = {
  id: 'note-001',
  content: 'Finish the roadmap',
  source: 'text',
  category_id: 'cat-001',
  category: TEST_CATEGORY,
  created_at: '2026-04-06T10:00:00Z',
  updated_at: '2026-04-06T10:00:00Z',
}

export const TEST_PAGINATED: PaginatedNotes = {
  items: [TEST_NOTE],
  total: 1,
  page: 1,
  limit: 50,
}

export const TEST_NOTE_CREATE_RESPONSE: NoteCreateResponse = {
  note: TEST_NOTE,
  category: TEST_CATEGORY,
  action: null,
}

export const TEST_INTEGRATIONS: IntegrationStatus[] = [
  { service: 'google_calendar', connected: false },
  { service: 'gmail', connected: false },
  { service: 'notion', connected: false },
]

// Must match VITE_API_BASE_URL from .env (http://localhost:8000/api/v1)
const BASE = 'http://localhost:8000/api/v1'

export const handlers = [
  http.get(`${BASE}/auth/me`, () => HttpResponse.json(TEST_USER)),
  http.post(`${BASE}/auth/google`, () =>
    HttpResponse.json({ access_token: 'test-jwt-token', user: TEST_USER }),
  ),
  http.post(`${BASE}/auth/dev-login`, () =>
    HttpResponse.json({ access_token: 'dev-jwt-token', user: { ...TEST_USER, email: 'dev@kaikoo.local' } }),
  ),
  http.get(`${BASE}/notes`, () => HttpResponse.json(TEST_PAGINATED)),
  http.post(`${BASE}/notes`, () => HttpResponse.json(TEST_NOTE_CREATE_RESPONSE)),
  http.delete(`${BASE}/notes/:id`, () => HttpResponse.json({ ok: true })),
  http.get(`${BASE}/categories`, () => HttpResponse.json([TEST_CATEGORY])),
  http.delete(`${BASE}/categories/:id`, () => HttpResponse.json({ ok: true })),
  http.get(`${BASE}/integrations`, () => HttpResponse.json(TEST_INTEGRATIONS)),
]

export const server = setupServer(...handlers)
