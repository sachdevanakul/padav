import {
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { ChartCard } from './ChartCard'
import type { TrendDataPoint } from './types'
import { useReducedMotion } from '../../hooks/useReducedMotion'

type LineChartProps = {
  data: TrendDataPoint[]
  title: string
  subtitle?: string
  height?: number
  loading?: boolean
  colorKey?: 'primary' | 'blue' | 'mint' | 'purple' | 'orange' | 'sky' | 'danger'
  emptyMessage?: string
}

export function LineChartComponent({
  data,
  title,
  subtitle,
  height = 280,
  loading = false,
  colorKey = 'primary',
  emptyMessage,
}: LineChartProps) {
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
        <LineChart
          data={data}
          margin={{ top: 20, right: 20, bottom: 20, left: 0 }}
        >
          <defs>
            <linearGradient id={`lineGrad-${colorKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={`var(--${colorKey})`} stopOpacity={0.3} />
              <stop offset="100%" stopColor={`var(--${colorKey})`} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--grid)" strokeDasharray="4 5" />
          <XAxis
            dataKey="date"
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
            formatter={(value) => [value, 'Score']}
            cursor={{ fill: stroke }}
            separator=": "
            wrapperStyle={{ outline: 'none', boxShadow: 'none' }}
            contentStyle={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              color: 'var(--text)',
            }}
          />
          <Legend verticalAlign="top" align="right" />
          <Line
            type="monotone"
            dataKey="score"
            stroke={stroke}
            strokeWidth={2.5}
            fill="none"
            activeDot={{ r: 4, fill: stroke }}
            dot={{ r: 3, fill: stroke }}
            connectNulls
            isAnimationActive={!reducedMotion}
            animationDuration={reducedMotion ? 0 : 1500}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}