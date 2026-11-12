export type ChartTheme = 'primary' | 'blue' | 'mint' | 'purple' | 'orange' | 'sky' | 'danger';

export type ChartColorMap = Record<ChartTheme, string>;

export const CHART_COLORS: ChartColorMap = {
  primary: 'var(--primary)',
  blue: 'var(--blue)',
  mint: 'var(--mint)',
  purple: 'var(--purple)',
  orange: 'var(--orange)',
  sky: 'var(--sky)',
  danger: 'var(--danger)',
};

export type TrendDataPoint = {
  date: string;
  score: number;
  accuracy: number;
  questions_attempted: number;
};

export type DonutSegment = {
  name: string;
  value: number;
  color: ChartTheme;
};

export type BarDataPoint = {
  name: string;
  value: number;
};