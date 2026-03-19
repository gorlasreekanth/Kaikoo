import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Sparkles, ArrowLeft } from 'lucide-react'
import { useCategories } from '../hooks/useCategories'
import { NoteInput } from '../components/notes/NoteInput'
import { NoteList } from '../components/notes/NoteList'
import { ConfirmationModal } from '../components/confirmation/ConfirmationModal'
import { Button } from '../components/ui/Button'
import { CategoryBadge } from '../components/notes/CategoryBadge'
import type { NoteAction } from '../api/types'

export function CategoryPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: categories } = useCategories()
  const category = categories?.find((c) => c.id === id)
  const [pendingAction, setPendingAction] = useState<NoteAction | null>(null)
  const [pendingNoteId, setPendingNoteId] = useState<string | null>(null)

  const handleAction = (action: NoteAction, noteId: string) => {
    setPendingAction(action)
    setPendingNoteId(noteId)
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/')} className="text-text-muted hover:text-text transition-colors cursor-pointer">
          <ArrowLeft className="size-4" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2.5 mb-0.5">
            {category && <CategoryBadge name={category.name} color={category.color} />}
            <span className="text-text-muted text-sm">{category?.note_count ?? 0} notes</span>
          </div>
        </div>
        {id && (
          <Button variant="ghost" size="sm" onClick={() => navigate(`/summary/${id}`)} className="gap-1.5">
            <Sparkles className="size-3.5" />
            Summarize
          </Button>
        )}
      </div>
      <NoteInput onAction={handleAction} />
      <NoteList categoryId={id} />
      <ConfirmationModal action={pendingAction} noteId={pendingNoteId} onClose={() => { setPendingAction(null); setPendingNoteId(null) }} />
    </div>
  )
}
