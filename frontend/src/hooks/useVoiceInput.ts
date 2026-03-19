import { useCallback, useEffect, useRef, useState } from 'react'

interface UseVoiceInputResult {
  transcript: string
  isListening: boolean
  isSupported: boolean
  error: string | null
  start: () => void
  stop: () => void
  reset: () => void
}

type SpeechRecognitionConstructor = new () => SpeechRecognition

function getSpeechRecognition(): SpeechRecognitionConstructor | undefined {
  if (typeof window === 'undefined') return undefined
  return (
    (window as Window & { SpeechRecognition?: SpeechRecognitionConstructor }).SpeechRecognition ??
    (window as Window & { webkitSpeechRecognition?: SpeechRecognitionConstructor }).webkitSpeechRecognition
  )
}

export function useVoiceInput(onTranscript?: (text: string) => void): UseVoiceInputResult {
  const [transcript, setTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  const SpeechRecognitionCtor = getSpeechRecognition()
  const isSupported = Boolean(SpeechRecognitionCtor)

  useEffect(() => {
    if (!SpeechRecognitionCtor) return

    const recognition = new SpeechRecognitionCtor()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript
        if (event.results[i].isFinal) final += text
        else interim += text
      }
      const combined = final || interim
      setTranscript(combined)
      if (final && onTranscript) onTranscript(final)
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setError(`Voice error: ${event.error}`)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    return () => recognition.abort()
  }, [isSupported])

  const start = useCallback(() => {
    if (!recognitionRef.current) return
    setError(null)
    setTranscript('')
    recognitionRef.current.start()
    setIsListening(true)
  }, [])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const reset = useCallback(() => {
    setTranscript('')
    setError(null)
  }, [])

  return { transcript, isListening, isSupported, error, start, stop, reset }
}
