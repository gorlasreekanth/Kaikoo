import { apiClient } from './client'

export interface LLMSettings {
  provider: string | null
  has_api_key: boolean
  model: string | null
}

export interface LLMSettingsUpdate {
  provider?: string | null
  api_key?: string | null
  model?: string | null
}

export async function getLLMSettings(): Promise<LLMSettings> {
  const { data } = await apiClient.get<LLMSettings>('/llm-settings')
  return data
}

export async function updateLLMSettings(body: LLMSettingsUpdate): Promise<LLMSettings> {
  const { data } = await apiClient.put<LLMSettings>('/llm-settings', body)
  return data
}

export interface TestResult {
  ok: boolean
  message: string
}

export async function testLLMConnection(): Promise<TestResult> {
  const { data } = await apiClient.post<TestResult>('/llm-settings/test')
  return data
}
