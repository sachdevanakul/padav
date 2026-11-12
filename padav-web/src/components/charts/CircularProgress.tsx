import { ChartCard } from './ChartCard'

type CircularProgressProps = {
  title: string
  subtitle?: string
  value: number // 0-100
  label: string
  colorKey?: 'primary' | 'blue' | 'mint' | 'purple' | 'orange' | 'sky' | 'danger'
  loading?: boolean
}

export function CircularProgress({
  title,
  subtitle,
  value,
  label,
  colorKey = 'primary',
  loading = false,
}: CircularProgressProps) {
  const stroke = `var(--${colorKey})`
  const clamped = Math.max(0, Math.min(100, value))
  const circumference = 2 * Math.PI * 45 // radius 45
  const offset = circumference - (clamped / 100) * circumference

  if (loading) {
    return <ChartCard title={title} subtitle={subtitle} loading />
  }

  return (
    <ChartCard title={title} subtitle={subtitle}>
      <div className="pdv-circular-progress-wrap">
        <svg width="120" height="120">
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke="var(--border)"
            strokeWidth="10"
          />
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke={stroke}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
        <div className="pdv-circular-value">{clamped}%</div>
        <div className="pdv-circular-label">{label}</div>
      </div>
    </ChartCard>
  )
}