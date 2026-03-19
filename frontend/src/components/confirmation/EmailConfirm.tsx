import { useState } from 'react'
import { Mail } from 'lucide-react'
import { Button } from '../ui/Button'
import { sendEmail } from '../../api/integrations'
import { useToast } from '../ui/Toast'
import type { EmailAction } from '../../api/types'

interface EmailConfirmProps {
  action: EmailAction
  noteId: string
  onDone: () => void
}

export function EmailConfirm({ action, noteId, onDone }: EmailConfirmProps) {
  const { email } = action
  const [recipient, setRecipient] = useState(email.recipient_hint ?? '')
  const [subject, setSubject] = useState(email.subject ?? '')
  const [body, setBody] = useState(email.body ?? '')
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const handleSend = async (emailAction: 'send' | 'draft') => {
    setLoading(true)
    try {
      await sendEmail({ recipient, subject, body, note_id: noteId, action: emailAction })
      toast(emailAction === 'send' ? 'Email sent' : 'Draft saved to Gmail')
      onDone()
    } catch {
      toast('Failed to send email', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-accent text-sm font-medium">
        <Mail className="size-4" />
        Email detected
      </div>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-text-muted mb-1 block">To</label>
          <input
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="recipient@example.com"
            className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="text-xs text-text-muted mb-1 block">Subject</label>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="text-xs text-text-muted mb-1 block">Body</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
            className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text outline-none focus:border-accent resize-none"
          />
        </div>
      </div>
      <div className="flex gap-2 pt-1">
        <Button variant="ghost" size="sm" onClick={onDone} className="flex-1">Dismiss</Button>
        <Button variant="ghost" size="sm" onClick={() => handleSend('draft')} loading={loading} className="flex-1">Save Draft</Button>
        <Button size="sm" onClick={() => handleSend('send')} loading={loading} className="flex-1">Send</Button>
      </div>
    </div>
  )
}
