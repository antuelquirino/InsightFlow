"use client"

// Built on Recharts like the template's LineChart, which has no bar
// counterpart. Horizontal bars, 20px thick with a rounded data end, the value
// at the tip in ink (never in the bar's color), no grid.

import {
  Bar,
  BarChart as RechartsBarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"

import {
  type AvailableChartColorsKeys,
  type ChartDatum,
  cssColor,
} from "@/lib/chartUtils"
import type { Locale } from "@/lib/locale"
import { formatLabel, formatterFor, type ValueFormat } from "./valueFormats"

export function BarChart({
  data,
  index,
  category,
  valueFormat,
  colors,
  locale = "en",
  className,
}: {
  data: ChartDatum[]
  index: string
  category: string
  valueFormat: ValueFormat
  /** One color per row; defaults to the accent for every bar (one series). */
  colors?: AvailableChartColorsKeys[]
  locale?: Locale
  className?: string
}) {
  const format = formatterFor(valueFormat, locale)
  const rowHeight = 40
  return (
    <div
      className={className}
      style={{ height: Math.max(data.length * rowHeight + 16, 120) }}
    >
      <ResponsiveContainer>
        <RechartsBarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 72, bottom: 0, left: 0 }}
        >
          <XAxis type="number" hide domain={[0, "dataMax"]} />
          <YAxis
            type="category"
            dataKey={index}
            width={124}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "var(--graphite)", fontSize: 13 }}
            tickFormatter={(value) => formatLabel(value, locale)}
          />
          <Bar
            dataKey={category}
            barSize={20}
            radius={[0, 4, 4, 0]}
            isAnimationActive={false}
          >
            {data.map((_, row) => (
              <Cell key={row} fill={cssColor(colors?.[row] ?? "ochre")} />
            ))}
            <LabelList
              dataKey={category}
              position="right"
              offset={8}
              formatter={(value) =>
                typeof value === "number" ? format(value) : ""
              }
              style={{
                fill: "var(--ink)",
                fontSize: 13,
                fontVariantNumeric: "tabular-nums",
              }}
            />
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  )
}
