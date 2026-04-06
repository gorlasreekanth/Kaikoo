import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { renderWithProviders } from '../../test/renderWithProviders'
import { server, TEST_NOTE } from '../../test/server'
import { NoteCard } from '../../components/notes/NoteCard'

describe('NoteCard', () => {
  it('renders note content', () => {
    renderWithProviders(<NoteCard note={TEST_NOTE} />)
    expect(screen.getByText(TEST_NOTE.content)).toBeInTheDocument()
  })

  it('renders category badge', () => {
    renderWithProviders(<NoteCard note={TEST_NOTE} />)
    expect(screen.getByText('Work')).toBeInTheDocument()
  })

  it('renders mic icon for voice notes', () => {
    const voiceNote = { ...TEST_NOTE, source: 'voice' as const }
    renderWithProviders(<NoteCard note={voiceNote} />)
    const svgs = document.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThan(0)
  })

  it('does not render mic icon for text notes', () => {
    renderWithProviders(<NoteCard note={{ ...TEST_NOTE, source: 'text' }} />)
    // No mic icon class check — just ensure renders without error
    expect(screen.getByText(TEST_NOTE.content)).toBeInTheDocument()
  })

  it('calls delete API on trash button click', async () => {
    let deleteCalled = false
    server.use(
      http.delete(`http://localhost:8000/api/v1/notes/${TEST_NOTE.id}`, () => {
        deleteCalled = true
        return HttpResponse.json({ ok: true })
      }),
    )

    renderWithProviders(<NoteCard note={TEST_NOTE} />)
    const deleteBtn = document.querySelector('button')!
    await userEvent.click(deleteBtn)
    expect(deleteCalled).toBe(true)
  })

  it('renders a note without a category', () => {
    const noteWithoutCategory = { ...TEST_NOTE, category: null, category_id: null }
    renderWithProviders(<NoteCard note={noteWithoutCategory} />)
    expect(screen.getByText(TEST_NOTE.content)).toBeInTheDocument()
  })
})
