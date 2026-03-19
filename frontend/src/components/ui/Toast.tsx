import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle, XCircle, X } from 'lucide-react'
import { cn } from '../../utils/cn'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error'
}

interface ToastContextValue {
  toast: (message: string, type?: 'success' | 'error') => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              'flex items-center gap-2.5 px-4 py-3 rounded-lg border text-sm font-medium shadow-lg',
              t.type === 'success' ? 'bg-surface border-success/30 text-success' : 'bg-surface border-danger/30 text-danger'
            )}
          >
            {t.type === 'success' ? <CheckCircle className="size-4 shrink-0" /> : <XCircle className="size-4 shrink-0" />}
            <span className="text-text">{t.message}</span>
            <button onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))} className="ml-auto text-text-muted hover:text-text cursor-pointer">
              <X className="size-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
