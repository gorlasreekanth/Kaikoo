import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatRelativeDate, formatDateTime } from '../../utils/formatDate'

const NOW = new Date('2026-04-06T12:00:00Z')

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(NOW)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('formatRelativeDate', () => {
  it('returns "just now" for < 1 minute ago', () => {
    const date = new Date(NOW.getTime() - 30_000).toISOString()
    expect(formatRelativeDate(date)).toBe('just now')
  })

  it('returns minutes for < 1 hour ago', () => {
    const date = new Date(NOW.getTime() - 5 * 60_000).toISOString()
    expect(formatRelativeDate(date)).toBe('5m ago')
  })

  it('returns hours for < 24 hours ago', () => {
    const date = new Date(NOW.getTime() - 3 * 3_600_000).toISOString()
    expect(formatRelativeDate(date)).toBe('3h ago')
  })

  it('returns "yesterday" for exactly 1 day ago', () => {
    const date = new Date(NOW.getTime() - 1 * 86_400_000 - 1).toISOString()
    expect(formatRelativeDate(date)).toBe('yesterday')
  })

  it('returns days for < 7 days ago', () => {
    const date = new Date(NOW.getTime() - 4 * 86_400_000).toISOString()
    expect(formatRelativeDate(date)).toBe('4d ago')
  })

  it('returns formatted date for >= 7 days ago', () => {
    const date = new Date(NOW.getTime() - 10 * 86_400_000).toISOString()
    const result = formatRelativeDate(date)
    expect(result).toMatch(/Mar/)
  })
})

describe('formatDateTime', () => {
  it('returns a non-empty string', () => {
    expect(formatDateTime(NOW.toISOString())).toBeTruthy()
  })

  it('includes the day number', () => {
    expect(formatDateTime(NOW.toISOString())).toContain('6')
  })
})
