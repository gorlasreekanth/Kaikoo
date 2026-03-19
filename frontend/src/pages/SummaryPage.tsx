import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { getSummary } from '../api/integrations'
import { useCategories } from '../hooks/useCategories'
import { Spinner } from '../components/ui/Spinner'
import { formatDateTime } from '../utils/formatDate'

export function SummaryPage() {
  const { category_id } = useParams<{ category_id: string }>()
  const navigate = useNavigate()
  const { data: categories } = useCategories()
  const category = categories?.find((c) => c.id === category_id)

  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', category_id],
    queryFn: () => getSummary(category_id!),
    enabled: Boolean(category_id),
  })

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate(-1)} className="text-text-muted hover:text-text transition-colors cursor-pointer">
          <ArrowLeft className="size-4" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-accent" />
            <span className="font-semibold text-text">{category?.name ?? 'Summary'}</span>
          </div>
          <p className="text-text-muted text-xs mt-0.5">AI-generated summary</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : summary ? (
        <div className="space-y-4">
          <div className="bg-surface border border-border rounded-xl p-6">
            <p className="text-text text-sm leading-relaxed whitespace-pre-wrap">{summary.summary}</p>
          </div>
          <div className="flex items-center justify-between text-text-muted text-xs px-1">
            <span>{summary.note_count} notes summarized</span>
            <span>Generated {formatDateTime(summary.generated_at)}</span>
          </div>
        </div>
      ) : (
        <p className="text-text-muted text-sm">No summary available.</p>
      )}
    </div>
  )
}
