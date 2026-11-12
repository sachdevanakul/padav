import { useRef, useState, type ReactNode } from 'react'

type TooltipProps = {
  children: ReactNode
  text: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
  className?: string
}

export function Tooltip({ children, text, placement = 'top', delay = 0, className = '' }: TooltipProps) {
  const [show, setShow] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function showTooltip() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setShow(true), delay)
  }

  function hideTooltip() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = null
    setShow(false)
  }

  return <span
    className={`pdv-tooltip-root ${className}`}
    onMouseEnter={showTooltip}
    onMouseLeave={hideTooltip}
    onFocus={showTooltip}
    onBlur={hideTooltip}
  >
    {children}
    {show && <span className="pdv-tooltip" role="tooltip" data-placement={placement}>{text}</span>}
  </span>
}
