import { Trash2, Mic } from 'lucide-react'
import { CategoryBadge } from './CategoryBadge'
import { formatRelativeDate } from '../../utils/formatDate'
import { useDeleteNote } from '../../hooks/useNotes'
import { useToast } from '../ui/Toast'
import type { Note } from '../../api/types'

interface NoteCardProps {
  note: Note
}

export function NoteCard({ note }: NoteCardProps) {
  const deleteNote = useDeleteNote()
  const { toast } = useToast()

  const handleDelete = async () => {
    try {
      await deleteNote.mutateAsync(note.id)
      toast('Note deleted')
    } catch {
      toast('Failed to delete note', 'error')
    }
  }

  return (
    <div className="group bg-surface border border-border rounded-xl p-4 hover:border-accent/30 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <p className="text-text text-sm leading-relaxed whitespace-pre-wrap flex-1">{note.content}</p>
        <button
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 transition-opacity text-text-muted hover:text-danger cursor-pointer shrink-0 mt-0.5"
        >
          <Trash2 className="size-3.5" />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-3">
        {note.category && (
          <CategoryBadge name={note.category.name} color={note.category.color} size="xs" />
        )}
        <span className="text-text-muted text-[11px] ml-auto flex items-center gap-1">
          {note.source === 'voice' && <Mic className="size-2.5" />}
          {formatRelativeDate(note.created_at)}
        </span>
      </div>
    </div>
  )
}
