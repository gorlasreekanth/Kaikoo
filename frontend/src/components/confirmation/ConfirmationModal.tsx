import { Modal } from '../ui/Modal'
import { CalendarConfirm } from './CalendarConfirm'
import { EmailConfirm } from './EmailConfirm'
import type { NoteAction } from '../../api/types'

interface ConfirmationModalProps {
  action: NoteAction | null
  noteId: string | null
  onClose: () => void
}

export function ConfirmationModal({ action, noteId, onClose }: ConfirmationModalProps) {
  if (!action || !noteId) return null

  const title = action.type === 'calendar' ? 'Add Calendar Event?' : 'Send Email?'

  return (
    <Modal open={true} onClose={onClose} title={title}>
      {action.type === 'calendar' ? (
        <CalendarConfirm action={action} noteId={noteId} onDone={onClose} />
      ) : (
        <EmailConfirm action={action} noteId={noteId} onDone={onClose} />
      )}
    </Modal>
  )
}
