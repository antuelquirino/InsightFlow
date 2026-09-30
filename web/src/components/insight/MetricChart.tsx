"use client"

import { LineChart } from "@/components/LineChart"
import type { AvailableChartColorsKeys, ChartDatum } from "@/lib/chartUtils"
import {
  formatCurrency,
  formatMonth,
  formatNumber,
  formatPercent,
  formatRatio,
} from "@/lib/format"

// Server components cannot pass functions to client components, so charts
// receive the name of a format and look the formatter up here.
export type ValueFormat = "currency" | "percent" | "number" | "ratio"

const VALUE_FORMATTERS: Record<ValueFormat, (value: number) => string> = {
  currency: (value) => formatCurrency(value),
  percent: (value) => formatPercent(value),
  number: (value) => formatNumber(value),
  ratio: (value) => formatRatio(value),
}

/** A monthly line chart on the design system: months on the x axis, one format for values. */
export function MetricLineChart({
  data,
  categories,
  colors,
  valueFormat,
  showLegend,
  className,
}: {
  data: ChartDatum[]
  categories: string[]
  colors?: AvailableChartColorsKeys[]
  valueFormat: ValueFormat
  showLegend?: boolean
  className?: string
}) {
  return (
    <LineChart
      data={data}
      index="month"
      categories={categories}
      colors={colors}
      valueFormatter={VALUE_FORMATTERS[valueFormat]}
      indexFormatter={(month) => formatMonth(month)}
      // a single series needs no legend: the section title names it
      showLegend={showLegend ?? categories.length > 1}
      yAxisWidth={56}
      className={className ?? "h-72"}
    />
  )
}
