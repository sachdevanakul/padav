import { useMemo } from 'react'
import { Pie, PieChart, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { ChartCard } from './ChartCard'
import type { DonutSegment } from './types'
import { useReducedMotion } from '../../hooks/useReducedMotion'

type DonutChartProps = {
  data: DonutSegment[]
  title: string
  subtitle?: string
  centerLabel: string
  centerValue: string | number
  height?: number
  loading?: boolean
  emptyMessage?: string
}

export function DonutChartComponent({
  data,
  title,
  subtitle,
  centerLabel,
  centerValue,
  height = 260,
  loading = false,
  emptyMessage,
}: DonutChartProps) {
  const total = useMemo(() => data.reduce((sum, item) => sum + item.value, 0), [data])
  const reducedMotion = useReducedMotion()

  if (loading) {
    return (
      <ChartCard title={title} subtitle={subtitle} loading />
    )
  }

  if (data.length === 0) {
    return (
      <ChartCard title={title} subtitle={subtitle} empty emptyMessage={emptyMessage} />
    )
  }

  return (
    <ChartCard title={title} subtitle={subtitle}>
      <div className="pdv-donut-wrap">
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data.map((d) => ({ name: d.name, value: d.value }))}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={80}
              outerRadius={100}
              isAnimationActive={!reducedMotion}
              animationDuration={reducedMotion ? 0 : 1500}
              animationEasing="ease-out"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={`var(--${entry.color})`} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => {
                const count = Number(value)
                const percent = total ? Math.round(count / total * 100) : 0
                return [`${count} (${percent}%)`, 'Attempts']
              }}
              contentStyle={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                color: 'var(--text)',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pdv-donut-center">
          <div className="pdv-donut-value">{centerValue}</div>
          <div className="pdv-donut-label">{centerLabel}</div>
        </div>
      </div>
    </ChartCard>
  )
}