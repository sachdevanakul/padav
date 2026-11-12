import type { ReactNode } from 'react'
import { Target } from 'lucide-react'

type ChartCardProps = {
  title: string
  subtitle?: string
  icon?: ReactNode
  children?: ReactNode
  loading?: boolean
  empty?: boolean
  emptyMessage?: string
  className?: string
}

export function ChartCard({
  title,
  subtitle,
  icon,
  children,
  loading = false,
  empty = false,
  emptyMessage = 'No data available',
  className,
}: ChartCardProps) {
  const EmptyIcon = icon || <Target size={48} />

  if (loading) {
    return (
      <div className={`pdv-chart-card pdv-chart-skeleton ${className ?? ''}`} />
    )
  }

  if (empty) {
    return (
      <div className={`pdv-chart-card ${className ?? ''}`}>
        <div className="pdv-chart-empty">
          <span className="pdv-chart-empty-icon">{EmptyIcon}</span>
          <p>{emptyMessage}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`pdv-chart-card ${className ?? ''}`}>
      <div className="pdv-chart-header">
        <div>
          {icon && <span className="pdv-chart-subtitle pdv-flex pdv-items-center pdv-gap-2 pdv-mb-2">{icon}</span>}
          <h3 className="pdv-chart-title">{title}</h3>
          {subtitle && <p className="pdv-chart-subtitle">{subtitle}</p>}
        </div>
      </div>
      <div className="pdv-chart-wrap">{children}</div>
    </div>
  )
}