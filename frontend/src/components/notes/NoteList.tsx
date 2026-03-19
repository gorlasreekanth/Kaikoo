import { FileText } from 'lucide-react'
import { NoteCard } from './NoteCard'
import { Spinner } from '../ui/Spinner'
import { EmptyState } from '../ui/EmptyState'
import { useNotes } from '../../hooks/useNotes'

interface NoteListProps {
  categoryId?: string
}

export function NoteList({ categoryId }: NoteListProps) {
  const { data, isLoading } = useNotes(categoryId)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    )
  }

  const notes = data?.items ?? []

  if (notes.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No notes yet"
        description="Add your first note using the input above"
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {notes.map((note) => (
        <NoteCard key={note.id} note={note} />
      ))}
    </div>
  )
}
