import { useRef, useState, type FormEvent } from 'react'
import { Send } from 'lucide-react'
import { VoiceButton } from './VoiceButton'
import { Button } from '../ui/Button'
import { useVoiceInput } from '../../hooks/useVoiceInput'
import { useCreateNote } from '../../hooks/useNotes'
import { useToast } from '../ui/Toast'
import type { NoteAction } from '../../api/types'

interface NoteInputProps {
  onAction?: (action: NoteAction, noteId: string) => void
}

export function NoteInput({ onAction }: NoteInputProps) {
  const [text, setText] = useState('')
  const [source, setSource] = useState<'text' | 'voice'>('text')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const createNote = useCreateNote()
  const { toast } = useToast()

  const voice = useVoiceInput((transcript) => {
    setText(transcript)
    setSource('voice')
  })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const content = text.trim()
    if (!content) return

    try {
      const result = await createNote.mutateAsync({ content, source })
      toast(`Note saved${result.category ? ` → ${result.category.name}` : ''}`)
      setText('')
      setSource('text')
      voice.reset()
      if (result.action && onAction) {
        onAction(result.action, result.note.id)
      }
    } catch {
      toast('Failed to save note', 'error')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e as unknown as FormEvent)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-surface border border-border rounded-xl p-4">
      <textarea
        ref={textareaRef}
        value={voice.isListening ? voice.transcript || text : text}
        onChange={(e) => { setText(e.target.value); setSource('text') }}
        onKeyDown={handleKeyDown}
        placeholder={voice.isListening ? 'Listening...' : 'What\'s on your mind? (⌘+Enter to save)'}
        rows={3}
        className="w-full bg-transparent text-text placeholder-text-muted text-sm resize-none outline-none leading-relaxed"
      />
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
        <VoiceButton
          isListening={voice.isListening}
          isSupported={voice.isSupported}
          onStart={voice.start}
          onStop={voice.stop}
        />
        {voice.error && <span className="text-danger text-xs">{voice.error}</span>}
        <Button
          type="submit"
          size="sm"
          loading={createNote.isPending}
          disabled={!text.trim() && !voice.transcript}
          className="ml-auto gap-1.5"
        >
          <Send className="size-3.5" />
          Save
        </Button>
      </div>
    </form>
  )
}
