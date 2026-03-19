import { cn } from '../../utils/cn'

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      className={cn('size-5 border-2 border-border border-t-accent rounded-full animate-spin', className)}
    />
  )
}
