import { describe, it, expect, vi } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '../../test/renderWithProviders'
import { server, TEST_NOTE_CREATE_RESPONSE } from '../../test/server'
import { NoteInput } from '../../components/notes/NoteInput'

describe('NoteInput', () => {
  it('renders the textarea', () => {
    renderWithProviders(<NoteInput />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('Save button is disabled when textarea is empty', () => {
    renderWithProviders(<NoteInput />)
    expect(screen.getByRole('button', { name: /save/i })).toBeDisabled()
  })

  it('Save button is enabled after typing', async () => {
    renderWithProviders(<NoteInput />)
    await userEvent.type(screen.getByRole('textbox'), 'Hello')
    expect(screen.getByRole('button', { name: /save/i })).not.toBeDisabled()
  })

  it('submits the form and clears the textarea', async () => {
    renderWithProviders(<NoteInput />)
    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'My note content')
    await userEvent.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('')
    })
  })

  it('calls onAction when API returns an action', async () => {
    const onAction = vi.fn()
    const calendarResponse = {
      ...TEST_NOTE_CREATE_RESPONSE,
      action: {
        type: 'calendar' as const,
        calendar: { title: 'Team sync', start_time: '2026-04-07T10:00:00', end_time: '2026-04-07T10:30:00', description: '' },
      },
    }
    server.use(http.post('http://localhost:8000/api/v1/notes', () => HttpResponse.json(calendarResponse)))

    renderWithProviders(<NoteInput onAction={onAction} />)
    await userEvent.type(screen.getByRole('textbox'), 'Schedule team sync')
    await userEvent.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => expect(onAction).toHaveBeenCalledOnce())
    expect(onAction.mock.calls[0][0].type).toBe('calendar')
  })

  it('submits on Cmd+Enter', async () => {
    let called = false
    server.use(http.post('http://localhost:8000/api/v1/notes', () => { called = true; return HttpResponse.json(TEST_NOTE_CREATE_RESPONSE) }))

    renderWithProviders(<NoteInput />)
    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'Quick note')
    fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true })

    await waitFor(() => expect(called).toBe(true))
  })
})
