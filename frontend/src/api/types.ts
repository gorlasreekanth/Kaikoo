export interface User {
  id: string
  email: string
  name: string
  avatar_url: string | null
}

export interface Category {
  id: string
  name: string
  color: string
  note_count: number
  created_at: string
}

export interface CalendarAction {
  type: 'calendar'
  calendar: {
    title: string
    start_time: string
    end_time: string
    description: string
  }
}

export interface EmailAction {
  type: 'email'
  email: {
    recipient_hint: string
    subject: string
    body: string
  }
}

export type NoteAction = CalendarAction | EmailAction

export interface Note {
  id: string
  content: string
  source: 'text' | 'voice'
  category_id: string | null
  category: Category | null
  created_at: string
  updated_at: string
}

export interface NoteCreateResponse {
  note: Note
  category: Category
  action: NoteAction | null
}

export interface IntegrationStatus {
  service: 'google_calendar' | 'gmail' | 'notion'
  connected: boolean
  email?: string
}

export interface Summary {
  summary: string
  note_count: number
  generated_at: string
  category_name: string
}

export interface PaginatedNotes {
  items: Note[]
  total: number
  page: number
  limit: number
}
