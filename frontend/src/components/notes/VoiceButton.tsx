import { Mic, MicOff } from 'lucide-react'
import { cn } from '../../utils/cn'

interface VoiceButtonProps {
  isListening: boolean
  isSupported: boolean
  onStart: () => void
  onStop: () => void
}

export function VoiceButton({ isListening, isSupported, onStart, onStop }: VoiceButtonProps) {
  if (!isSupported) return null

  return (
    <button
      type="button"
      onClick={isListening ? onStop : onStart}
      className={cn(
        'p-2 rounded-lg transition-all cursor-pointer',
        isListening
          ? 'bg-danger/20 text-danger animate-pulse'
          : 'text-text-muted hover:text-text hover:bg-muted'
      )}
      title={isListening ? 'Stop recording' : 'Start voice input'}
    >
      {isListening ? <MicOff className="size-4" /> : <Mic className="size-4" />}
    </button>
  )
}
