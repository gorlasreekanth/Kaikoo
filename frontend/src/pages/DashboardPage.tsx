import { useState } from 'react'
import { NoteInput } from '../components/notes/NoteInput'
import { NoteList } from '../components/notes/NoteList'
import { ConfirmationModal } from '../components/confirmation/ConfirmationModal'
import type { NoteAction } from '../api/types'

export function DashboardPage() {
  const [pendingAction, setPendingAction] = useState<NoteAction | null>(null)
  const [pendingNoteId, setPendingNoteId] = useState<string | null>(null)

  const handleAction = (action: NoteAction, noteId: string) => {
    setPendingAction(action)
    setPendingNoteId(noteId)
  }

  const handleClose = () => {
    setPendingAction(null)
    setPendingNoteId(null)
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-text mb-1">All Notes</h1>
        <p className="text-text-muted text-sm">Your thoughts, auto-organized by AI</p>
      </div>
      <NoteInput onAction={handleAction} />
      <NoteList />
      <ConfirmationModal action={pendingAction} noteId={pendingNoteId} onClose={handleClose} />
    </div>
  )
}
