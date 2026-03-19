import { useState } from 'react'
import { Calendar } from 'lucide-react'
import { Button } from '../ui/Button'
import { createCalendarEvent } from '../../api/integrations'
import { useToast } from '../ui/Toast'
import type { CalendarAction } from '../../api/types'

interface CalendarConfirmProps {
  action: CalendarAction
  noteId: string
  onDone: () => void
}

export function CalendarConfirm({ action, noteId, onDone }: CalendarConfirmProps) {
  const { calendar } = action
  const [title, setTitle] = useState(calendar.title)
  const [startTime, setStartTime] = useState(calendar.start_time?.slice(0, 16) ?? '')
  const [endTime, setEndTime] = useState(calendar.end_time?.slice(0, 16) ?? '')
  const [description, setDescription] = useState(calendar.description ?? '')
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const handleConfirm = async () => {
    setLoading(true)
    try {
      await createCalendarEvent({ title, start_time: startTime, end_time: endTime, description, note_id: noteId })
      toast('Event added to Google Calendar')
      onDone()
    } catch {
      toast('Failed to create calendar event', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-accent text-sm font-medium">
        <Calendar className="size-4" />
        Calendar event detected
      </div>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-text-muted mb-1 block">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-text-muted mb-1 block">Start</label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">End</label>
            <input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-text-muted mb-1 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent resize-none"
          />
        </div>
      </div>
      <div className="flex gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onDone} className="flex-1">Dismiss</Button>
        <Button size="sm" onClick={handleConfirm} loading={loading} className="flex-1">Add to Calendar</Button>
      </div>
    </div>
  )
}
