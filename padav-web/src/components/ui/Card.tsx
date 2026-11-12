import type { KeyboardEvent, ReactNode } from 'react'

type CardVariant = 'default' | 'elevated' | 'outlined'

type CardProps = {
  variant?: CardVariant
  className?: string
  children: ReactNode
  header?: ReactNode
  footer?: ReactNode
  clickable?: boolean
  onClick?: () => void
}

export function Card({ variant = 'default', className, children, header, footer, clickable = false, onClick }: CardProps) {
  const variantStyles = {
    default: 'pdv-rounded-lg pdv-p-6',
    elevated: 'pdv-rounded-lg pdv-p-6 pdv-shadow-md pdv-transition-shadow',
    outlined: 'pdv-rounded-lg pdv-p-6 pdv-border pdv-border-gray-200',
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (clickable && onClick && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault()
      onClick()
    }
  }

  return (
    <div
      className={`
        ${variantStyles[variant]}
        ${className}
        ${clickable ? 'pdv-hover-lift pdv-transition-colors cursor-pointer' : ''}
        ${clickable && onClick ? 'pdv-focus-ring:focus-visible:outline-none' : ''}
      `}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={clickable ? onClick : undefined}
      onKeyDown={handleKeyDown}
    >
      {header && <div className="pdv-card-header pdv-mb-4">{header}</div>}
      <div className="pdv-card-body">{children}</div>
      {footer && <div className="pdv-card-footer pdv-text-right pdv-py-2">{footer}</div>}
    </div>
  )
}