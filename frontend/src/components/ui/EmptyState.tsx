import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="size-12 rounded-full bg-muted flex items-center justify-center mb-4">
        <Icon className="size-5 text-text-muted" />
      </div>
      <p className="text-text font-medium text-sm">{title}</p>
      {description && <p className="text-text-muted text-xs mt-1 max-w-xs">{description}</p>}
    </div>
  )
}
