"use client"

import { LineChart } from "@/components/LineChart"
import type { AvailableChartColorsKeys, ChartDatum } from "@/lib/chartUtils"
import { formatLabel, VALUE_FORMATTERS, type ValueFormat } from "./valueFormats"

export type { ValueFormat } from "./valueFormats"

/** A monthly line chart on the design system: months on the x axis, one format for values. */
export function MetricLineChart({
  data,
  categories,
  colors,
  valueFormat,
  index = "month",
  showLegend,
  className,
}: {
  data: ChartDatum[]
  categories: string[]
  colors?: AvailableChartColorsKeys[]
  valueFormat: ValueFormat
  index?: string
  showLegend?: boolean
  className?: string
}) {
  return (
    <LineChart
      data={data}
      index={index}
      categories={categories}
      colors={colors}
      valueFormatter={VALUE_FORMATTERS[valueFormat]}
      indexFormatter={formatLabel}
      // a single series needs no legend: the section title names it
      showLegend={showLegend ?? categories.length > 1}
      yAxisWidth={56}
      className={className ?? "h-72"}
    />
  )
}
