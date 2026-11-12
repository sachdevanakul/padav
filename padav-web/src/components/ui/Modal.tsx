import { useEffect, useRef, type MouseEvent, type ReactNode } from 'react'

type ModalProps = {
  isOpen: boolean
  onClose: () => void
  title?: string
  ariaLabelledBy?: string
  role?: 'dialog' | 'alertdialog'
  children: ReactNode
  showCloseButton?: boolean
  destroyOnClose?: boolean
  dismissible?: boolean
  className?: string
}

export function Modal({
  isOpen,
  onClose,
  title,
  ariaLabelledBy,
  role = 'dialog',
  children,
  showCloseButton = true,
  dismissible = true,
  className = '',
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return
    const previousOverflow = document.body.style.overflow
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    document.body.style.overflow = 'hidden'
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dismissible) {
        onClose()
        return
      }
      if (event.key !== 'Tab' || !modalRef.current) return
      const focusable = modalRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
      )
      if (focusable.length === 0) {
        event.preventDefault()
        modalRef.current.focus()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first || !modalRef.current.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || !modalRef.current.contains(document.activeElement))) {
        event.preventDefault()
        first.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    const initialFocus = modalRef.current?.querySelector<HTMLElement>(
      'input:not(:disabled), select:not(:disabled), textarea:not(:disabled), button:not(:disabled), a[href]',
    )
    if (initialFocus) initialFocus.focus()
    else modalRef.current?.focus()
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeyDown)
      if (previouslyFocused?.isConnected) previouslyFocused.focus()
    }
  }, [dismissible, isOpen, onClose])

  if (!isOpen) {
    return null
  }

  return (
    <div
      className="pdv-modal-backdrop"
      onClick={(e: MouseEvent<HTMLDivElement>) => {
        if (dismissible && e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={modalRef}
        className={`pdv-modal-panel ${className}`}
        role={role}
        aria-modal="true"
        aria-labelledby={ariaLabelledBy}
        aria-label={ariaLabelledBy ? undefined : title}
        tabIndex={-1}
      >
        {showCloseButton && <button type="button" className="icon-button" onClick={onClose} aria-label="Close dialog">×</button>}
        {children}
      </div>
    </div>
  )
}