import { NavLink } from 'react-router-dom'
import { Settings, Hash, Home } from 'lucide-react'
import { useCategories } from '../../hooks/useCategories'
import { cn } from '../../utils/cn'

export function Sidebar() {
  const { data: categories } = useCategories()

  return (
    <aside className="w-56 shrink-0 border-r border-border flex flex-col h-full">
      <div className="px-4 py-5 border-b border-border">
        <span className="text-text font-semibold text-base tracking-tight">Kaikoo</span>
      </div>

      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-0.5">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            cn('flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
              isActive ? 'bg-accent/10 text-accent' : 'text-text-muted hover:text-text hover:bg-muted')
          }
        >
          <Home className="size-4 shrink-0" />
          All Notes
        </NavLink>

        {categories && categories.length > 0 && (
          <div className="mt-4 mb-1 px-3">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Categories</span>
          </div>
        )}

        {categories?.map((cat) => (
          <NavLink
            key={cat.id}
            to={`/category/${cat.id}`}
            className={({ isActive }) =>
              cn('flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive ? 'bg-accent/10 text-accent' : 'text-text-muted hover:text-text hover:bg-muted')
            }
          >
            <Hash className="size-3.5 shrink-0" style={{ color: cat.color }} />
            <span className="truncate">{cat.name}</span>
            <span className="ml-auto text-[10px] text-text-muted">{cat.note_count}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-2 py-3 border-t border-border">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn('flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors',
              isActive ? 'bg-accent/10 text-accent' : 'text-text-muted hover:text-text hover:bg-muted')
          }
        >
          <Settings className="size-4 shrink-0" />
          Settings
        </NavLink>
      </div>
    </aside>
  )
}
