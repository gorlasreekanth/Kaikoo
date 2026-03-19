import { apiClient } from './client'
import type { Category } from './types'

export async function getCategories(): Promise<Category[]> {
  const { data } = await apiClient.get('/categories')
  return data
}

export async function deleteCategory(id: string): Promise<void> {
  await apiClient.delete(`/categories/${id}`)
}
