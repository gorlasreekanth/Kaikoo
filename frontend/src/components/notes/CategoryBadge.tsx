interface CategoryBadgeProps {
  name: string
  color?: string
  size?: 'sm' | 'xs'
}

export function CategoryBadge({ name, color = '#7c6af7', size = 'sm' }: CategoryBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${size === 'xs' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'}`}
      style={{ backgroundColor: `${color}22`, color }}
    >
      {name}
    </span>
  )
}
