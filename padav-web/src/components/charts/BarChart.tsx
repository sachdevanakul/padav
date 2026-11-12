import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { ChartCard } from './ChartCard'
import { useReducedMotion } from '../../hooks/useReducedMotion'

type BarDataPoint = {
  name: string
  value: number
  fill?: string
}

type BarChartProps = {
  data: BarDataPoint[]
  title: string
  subtitle?: string
  height?: number
  loading?: boolean
  colorKey?: 'primary' | 'blue' | 'mint' | 'purple' | 'orange' | 'sky' | 'danger'
  emptyMessage?: string
}

export function BarChartComponent({
  data,
  title,
  subtitle,
  height = 280,
  loading = false,
  colorKey = 'primary',
  emptyMessage,
}: BarChartProps) {
  const stroke = `var(--${colorKey})`
  const reducedMotion = useReducedMotion()

  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      loading={loading}
      empty={!loading && data.length === 0}
      emptyMessage={emptyMessage}
    >
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
        >
          <CartesianGrid vertical={false} stroke="var(--grid)" strokeDasharray="4 5" />
          <XAxis
            dataKey="name"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--muted)', fontSize: 11 }}
            dy={9}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--muted)', fontSize: 10 }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            formatter={(value) => [value, 'Questions']}
            cursor={{ fill: stroke }}
            contentStyle={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              color: 'var(--text)',
            }}
          />
          <Legend verticalAlign="top" align="right" />
          <Bar
            dataKey="value"
            fill={stroke}
            radius={[4, 4, 0, 0]}
            isAnimationActive={!reducedMotion}
            animationDuration={reducedMotion ? 0 : 1200}
            animationEasing="ease-out"
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}