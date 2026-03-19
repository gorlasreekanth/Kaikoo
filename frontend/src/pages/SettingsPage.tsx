import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Calendar, Mail, BookOpen } from 'lucide-react'
import { IntegrationCard } from '../components/integrations/IntegrationCard'
import {
  getIntegrations,
  getCalendarAuthUrl,
  disconnectCalendar,
  getGmailAuthUrl,
  disconnectGmail,
  getNotionAuthUrl,
  disconnectNotion,
} from '../api/integrations'
import { useToast } from '../components/ui/Toast'

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { data: integrations = [] } = useQuery({
    queryKey: ['integrations'],
    queryFn: getIntegrations,
  })
  const { toast } = useToast()

  const isConnected = (service: string) =>
    integrations.find((i) => i.service === service)?.connected ?? false

  const openOAuth = (url: string) => window.open(url, '_blank', 'width=600,height=700')

  const handleConnect = async (getUrl: () => Promise<string>) => {
    try {
      const url = await getUrl()
      openOAuth(url)
    } catch {
      toast('Failed to start OAuth flow', 'error')
    }
  }

  const handleDisconnect = async (disconnect: () => Promise<void>, name: string) => {
    try {
      await disconnect()
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
      toast(`${name} disconnected`)
    } catch {
      toast(`Failed to disconnect ${name}`, 'error')
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-lg font-semibold text-text mb-1">Settings</h1>
        <p className="text-text-muted text-sm">Connect your apps to take action from notes</p>
      </div>

      <div className="space-y-3">
        <IntegrationCard
          icon={Calendar}
          name="Google Calendar"
          description="Auto-create calendar events from notes containing meeting details"
          connected={isConnected('google_calendar')}
          onConnect={() => handleConnect(getCalendarAuthUrl)}
          onDisconnect={() => handleDisconnect(disconnectCalendar, 'Google Calendar')}
        />
        <IntegrationCard
          icon={Mail}
          name="Gmail"
          description="Draft and send emails directly from your notes"
          connected={isConnected('gmail')}
          onConnect={() => handleConnect(getGmailAuthUrl)}
          onDisconnect={() => handleDisconnect(disconnectGmail, 'Gmail')}
        />
        <IntegrationCard
          icon={BookOpen}
          name="Notion"
          description="Sync your notes to Notion pages, organized by category"
          connected={isConnected('notion')}
          onConnect={() => handleConnect(getNotionAuthUrl)}
          onDisconnect={() => handleDisconnect(disconnectNotion, 'Notion')}
        />
      </div>
    </div>
  )
}
