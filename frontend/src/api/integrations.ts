import { apiClient } from './client'
import type { IntegrationStatus } from './types'

export async function getIntegrations(): Promise<IntegrationStatus[]> {
  const { data } = await apiClient.get('/integrations')
  return data
}

export async function getCalendarAuthUrl(): Promise<string> {
  const { data } = await apiClient.get('/calendar/auth-url')
  return data.url
}

export async function createCalendarEvent(payload: {
  title: string
  start_time: string
  end_time: string
  description: string
  note_id: string
}): Promise<{ event_url: string }> {
  const { data } = await apiClient.post('/calendar/events', payload)
  return data
}

export async function disconnectCalendar(): Promise<void> {
  await apiClient.delete('/calendar/disconnect')
}

export async function getGmailAuthUrl(): Promise<string> {
  const { data } = await apiClient.get('/gmail/auth-url')
  return data.url
}

export async function sendEmail(payload: {
  recipient: string
  subject: string
  body: string
  note_id: string
  action: 'send' | 'draft'
}): Promise<{ message_id: string }> {
  const { data } = await apiClient.post('/gmail/send', payload)
  return data
}

export async function disconnectGmail(): Promise<void> {
  await apiClient.delete('/gmail/disconnect')
}

export async function getNotionAuthUrl(): Promise<string> {
  const { data } = await apiClient.get('/notion/auth-url')
  return data.url
}

export async function disconnectNotion(): Promise<void> {
  await apiClient.delete('/notion/disconnect')
}

export async function getSummary(categoryId: string) {
  const { data } = await apiClient.get(`/summaries/${categoryId}`)
  return data
}
