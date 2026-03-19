import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createNote, deleteNote, getNotes } from '../api/notes'

export function useNotes(categoryId?: string) {
  return useQuery({
    queryKey: ['notes', categoryId],
    queryFn: () => getNotes({ category_id: categoryId, limit: 50 }),
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ content, source }: { content: string; source: 'text' | 'voice' }) =>
      createNote(content, source),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteNote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] })
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })
}
