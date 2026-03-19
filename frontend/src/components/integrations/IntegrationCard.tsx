import { ExternalLink, CheckCircle, XCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '../ui/Button'

interface IntegrationCardProps {
  icon: LucideIcon
  name: string
  description: string
  connected: boolean
  onConnect: () => void
  onDisconnect: () => void
  loading?: boolean
}

export function IntegrationCard({
  icon: Icon,
  name,
  description,
  connected,
  onConnect,
  onDisconnect,
  loading,
}: IntegrationCardProps) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5 flex items-start gap-4">
      <div className="size-10 rounded-xl bg-muted flex items-center justify-center shrink-0">
        <Icon className="size-5 text-text" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="font-medium text-text text-sm">{name}</span>
          {connected ? (
            <span className="flex items-center gap-1 text-success text-[11px] font-medium">
              <CheckCircle className="size-3" /> Connected
            </span>
          ) : (
            <span className="flex items-center gap-1 text-text-muted text-[11px]">
              <XCircle className="size-3" /> Not connected
            </span>
          )}
        </div>
        <p className="text-text-muted text-xs">{description}</p>
      </div>
      {connected ? (
        <Button variant="danger" size="sm" onClick={onDisconnect} loading={loading}>Disconnect</Button>
      ) : (
        <Button variant="ghost" size="sm" onClick={onConnect} loading={loading} className="gap-1.5">
          <ExternalLink className="size-3.5" />
          Connect
        </Button>
      )}
    </div>
  )
}
