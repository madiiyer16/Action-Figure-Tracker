'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export type ChartPoint = { date: string; [retailer: string]: number | string }

type PriceChartProps = {
  retailers: string[]
  data: ChartPoint[]
}

const COLORS = ['#60a5fa', '#34d399', '#f472b6', '#fbbf24']

function retailerLabel(retailer: string): string {
  const map: Record<string, string> = { amiami: 'AmiAmi', bbts: 'BigBadToyStore' }
  return map[retailer.toLowerCase()] ?? retailer
}

export default function PriceChart({ retailers, data }: PriceChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl h-48 flex items-center justify-center text-zinc-600 text-sm">
        No price history yet
      </div>
    )
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#71717a', fontSize: 11 }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#71717a', fontSize: 11 }}
            tickLine={false}
            tickFormatter={(v) => `$${v}`}
            width={50}
          />
          <Tooltip
            contentStyle={{
              background: '#18181b',
              border: '1px solid #3f3f46',
              borderRadius: 8,
            }}
            labelStyle={{ color: '#a1a1aa', marginBottom: 4 }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`]}
          />
          {retailers.length > 1 && (
            <Legend
              formatter={(value) => retailerLabel(value)}
              wrapperStyle={{ color: '#71717a', fontSize: 12 }}
            />
          )}
          {retailers.map((retailer, i) => (
            <Line
              key={retailer}
              type="monotone"
              dataKey={retailer}
              name={retailer}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3, fill: COLORS[i % COLORS.length] }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
