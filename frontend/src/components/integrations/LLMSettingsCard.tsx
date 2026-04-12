import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Brain, Eye, EyeOff, Check } from 'lucide-react'
import { Button } from '../ui/Button'
import { getLLMSettings, updateLLMSettings, testLLMConnection } from '../../api/llmSettings'
import { useToast } from '../ui/Toast'

const PROVIDERS = [
  { value: '', label: 'Default (OpenRouter)', hint: 'Free, no key needed' },
  { value: 'anthropic', label: 'Anthropic (Claude)', hint: 'Requires API key' },
  { value: 'openai', label: 'OpenAI (GPT)', hint: 'Requires API key' },
]

export function LLMSettingsCard() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const { data: settings } = useQuery({
    queryKey: ['llm-settings'],
    queryFn: getLLMSettings,
  })

  const [provider, setProvider] = useState<string>('')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [initialized, setInitialized] = useState(false)

  // Sync form state when settings load
  if (settings && !initialized) {
    setProvider(settings.provider ?? '')
    setInitialized(true)
  }

  const needsKey = provider === 'anthropic' || provider === 'openai'
  const hasExistingKey = settings?.has_api_key && settings?.provider === provider

  const handleSave = async () => {
    setSaving(true)
    try {
      const body: Record<string, string | null> = {
        provider: provider || null,
      }
      if (needsKey && apiKey) {
        body.api_key = apiKey
      } else if (!needsKey) {
        body.api_key = null
      }
      await updateLLMSettings(body)
      queryClient.invalidateQueries({ queryKey: ['llm-settings'] })
      setApiKey('')
      toast('AI provider updated')
    } catch {
      toast('Failed to update AI provider', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <div className="flex items-start gap-4 mb-4">
        <div className="size-10 rounded-xl bg-muted flex items-center justify-center shrink-0">
          <Brain className="size-5 text-text" />
        </div>
        <div className="flex-1 min-w-0">
          <span className="font-medium text-text text-sm">AI Provider</span>
          <p className="text-text-muted text-xs">
            Choose which AI processes your notes. Bring your own key or use the free default.
          </p>
        </div>
      </div>

      <div className="space-y-3 ml-14">
        {/* Provider select */}
        <div className="space-y-1.5">
          {PROVIDERS.map((p) => (
            <label
              key={p.value}
              className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${
                provider === p.value
                  ? 'border-accent bg-accent/5'
                  : 'border-border hover:border-text-muted/30'
              }`}
            >
              <input
                type="radio"
                name="provider"
                value={p.value}
                checked={provider === p.value}
                onChange={(e) => {
                  setProvider(e.target.value)
                  setApiKey('')
                }}
                className="sr-only"
              />
              <div className={`size-4 rounded-full border-2 flex items-center justify-center ${
                provider === p.value ? 'border-accent' : 'border-text-muted/40'
              }`}>
                {provider === p.value && <div className="size-2 rounded-full bg-accent" />}
              </div>
              <div className="flex-1">
                <span className="text-sm text-text">{p.label}</span>
                <span className="text-[11px] text-text-muted ml-2">{p.hint}</span>
              </div>
            </label>
          ))}
        </div>

        {/* API key input */}
        {needsKey && (
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted">API Key</label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={hasExistingKey ? 'Key saved — enter new key to replace' : 'Paste your API key'}
                className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"
              >
                {showKey ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            {hasExistingKey && !apiKey && (
              <p className="flex items-center gap-1 text-[11px] text-success">
                <Check className="size-3" /> Key is saved and encrypted
              </p>
            )}
          </div>
        )}

        {/* Save + Test buttons */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={handleSave}
            loading={saving}
            disabled={needsKey && !apiKey && !hasExistingKey}
          >
            Save
          </Button>
          <Button
            variant="ghost"
            size="sm"
            loading={testing}
            onClick={async () => {
              setTesting(true)
              setTestResult(null)
              try {
                const result = await testLLMConnection()
                setTestResult(result)
                toast(result.message, result.ok ? 'success' : 'error')
              } catch {
                setTestResult({ ok: false, message: 'Request failed' })
                toast('Connection test failed', 'error')
              } finally {
                setTesting(false)
              }
            }}
          >
            Test Connection
          </Button>
        </div>
        {testResult && (
          <p className={`text-[11px] ${testResult.ok ? 'text-success' : 'text-danger'}`}>
            {testResult.message}
          </p>
        )}
      </div>
    </div>
  )
}
