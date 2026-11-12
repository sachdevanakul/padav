import { useSyncExternalStore, type ReactNode } from 'react'

type ToastType = 'success' | 'error' | 'warning' | 'info'
type ToastAction = { label: string; onClick: () => void }
type Toast = {
  id: string
  message: string
  type: ToastType
  action?: ToastAction
  duration: number
}

let toasts: Toast[] = []
let nextId = 0
const listeners = new Set<() => void>()
const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function publish() {
  for (const listener of listeners) listener()
}

function getSnapshot() {
  return toasts
}

function ToastContainer() {
  const visibleToasts = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
  return <div className="pdv-toast-stack" aria-live="polite" aria-relevant="additions removals">
    {visibleToasts.map((toast) => <div key={toast.id} className={`pdv-toast is-${toast.type}`} role={toast.type === 'error' ? 'alert' : 'status'}>
      <p>{toast.message}</p>
      {toast.action && <button type="button" className="pdv-toast-action" onClick={toast.action.onClick}>{toast.action.label}</button>}
      <button type="button" className="pdv-toast-dismiss" onClick={() => removeToast(toast.id)} aria-label="Dismiss notification">×</button>
    </div>)}
  </div>
}

export function removeToast(id: string) {
  const timeout = toastTimeouts.get(id)
  if (timeout) clearTimeout(timeout)
  toastTimeouts.delete(id)
  const remaining = toasts.filter((toast) => toast.id !== id)
  if (remaining.length === toasts.length) return
  toasts = remaining
  publish()
}

export function showToast({
  message,
  type = 'info',
  action,
  duration = 5000,
}: {
  message: string
  type?: ToastType
  action?: ToastAction
  duration?: number
}) {
  const id = `toast-${++nextId}`
  toasts = [...toasts, { id, message, type, action, duration }]
  publish()
  if (duration > 0) toastTimeouts.set(id, setTimeout(() => removeToast(id), duration))
  return id
}

export default function ToastProvider({ children }: { children: ReactNode }) {
  return <>
    <ToastContainer />
    {children}
  </>
}
