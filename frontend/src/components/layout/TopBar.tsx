import { LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

export function TopBar() {
  const { user, logout } = useAuthStore()

  return (
    <header className="h-12 border-b border-border flex items-center justify-end px-6 shrink-0">
      <div className="flex items-center gap-3">
        {user?.avatar_url && (
          <img src={user.avatar_url} alt={user.name} className="size-7 rounded-full" />
        )}
        <span className="text-sm text-text-muted">{user?.name}</span>
        <button
          onClick={logout}
          className="text-text-muted hover:text-text transition-colors cursor-pointer"
          title="Log out"
        >
          <LogOut className="size-4" />
        </button>
      </div>
    </header>
  )
}
