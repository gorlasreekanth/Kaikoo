import { apiClient } from './client'
import type { Note, NoteCreateResponse, PaginatedNotes } from './types'

export async function createNote(content: string, source: 'text' | 'voice'): Promise<NoteCreateResponse> {
  const { data } = await apiClient.post('/notes', { content, source })
  return data
}

export async function getNotes(params?: { category_id?: string; page?: number; limit?: number }): Promise<PaginatedNotes> {
  const { data } = await apiClient.get('/notes', { params })
  return data
}

export async function getNote(id: string): Promise<Note> {
  const { data } = await apiClient.get(`/notes/${id}`)
  return data
}

export async function deleteNote(id: string): Promise<void> {
  await apiClient.delete(`/notes/${id}`)
}

export async function updateNote(id: string, content: string): Promise<Note> {
  const { data } = await apiClient.patch(`/notes/${id}`, { content })
  return data
}
