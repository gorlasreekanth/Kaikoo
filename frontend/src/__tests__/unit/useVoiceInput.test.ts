import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useVoiceInput } from '../../hooks/useVoiceInput'

describe('useVoiceInput — unsupported browser', () => {
  it('isSupported is false when SpeechRecognition is absent', () => {
    const { result } = renderHook(() => useVoiceInput())
    // jsdom has no SpeechRecognition by default
    expect(result.current.isSupported).toBe(false)
  })

  it('start() does nothing when unsupported', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(() => act(() => result.current.start())).not.toThrow()
    expect(result.current.isListening).toBe(false)
  })

  it('stop() does nothing when unsupported', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(() => act(() => result.current.stop())).not.toThrow()
  })

  it('reset() clears transcript and error', () => {
    const { result } = renderHook(() => useVoiceInput())
    act(() => result.current.reset())
    expect(result.current.transcript).toBe('')
    expect(result.current.error).toBeNull()
  })
})

describe('useVoiceInput — supported browser', () => {
  let mockRecognition: {
    start: ReturnType<typeof vi.fn>
    stop: ReturnType<typeof vi.fn>
    abort: ReturnType<typeof vi.fn>
    onresult: ((e: unknown) => void) | null
    onerror: ((e: unknown) => void) | null
    onend: (() => void) | null
    continuous: boolean
    interimResults: boolean
    lang: string
  }
  let MockSpeechRecognition: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockRecognition = {
      start: vi.fn(),
      stop: vi.fn(),
      abort: vi.fn(),
      onresult: null,
      onerror: null,
      onend: null,
      continuous: false,
      interimResults: false,
      lang: '',
    }
    // Must be a class (constructor function) for `new` to work with vitest mocks
    MockSpeechRecognition = vi.fn(function (this: typeof mockRecognition) {
      Object.assign(this, mockRecognition)
      mockRecognition = this as typeof mockRecognition
    })
    Object.defineProperty(window, 'SpeechRecognition', {
      value: MockSpeechRecognition,
      writable: true,
      configurable: true,
    })
  })

  it('isSupported is true when SpeechRecognition exists', () => {
    const { result } = renderHook(() => useVoiceInput())
    expect(result.current.isSupported).toBe(true)
  })

  it('start() calls recognition.start() and sets isListening', () => {
    const { result } = renderHook(() => useVoiceInput())
    act(() => result.current.start())
    expect(mockRecognition.start).toHaveBeenCalledOnce()
    expect(result.current.isListening).toBe(true)
  })

  it('stop() calls recognition.stop() and clears isListening', () => {
    const { result } = renderHook(() => useVoiceInput())
    act(() => result.current.start())
    act(() => result.current.stop())
    expect(mockRecognition.stop).toHaveBeenCalledOnce()
    expect(result.current.isListening).toBe(false)
  })

  it('onend sets isListening to false', () => {
    const { result } = renderHook(() => useVoiceInput())
    act(() => result.current.start())
    act(() => mockRecognition.onend?.())
    expect(result.current.isListening).toBe(false)
  })

  it('onerror sets error message', () => {
    const { result } = renderHook(() => useVoiceInput())
    act(() => mockRecognition.onerror?.({ error: 'network' }))
    expect(result.current.error).toContain('network')
    expect(result.current.isListening).toBe(false)
  })

  it('onresult updates transcript', () => {
    const onTranscript = vi.fn()
    const { result } = renderHook(() => useVoiceInput(onTranscript))

    const mockEvent = {
      resultIndex: 0,
      results: [
        Object.assign([{ transcript: 'hello world' }], { isFinal: true }),
      ],
    }
    act(() => mockRecognition.onresult?.(mockEvent))
    expect(result.current.transcript).toBe('hello world')
    expect(onTranscript).toHaveBeenCalledWith('hello world')
  })
})
