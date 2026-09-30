"use client"

import { LineChart } from "@/components/LineChart"
import type { AvailableChartColorsKeys, ChartDatum } from "@/lib/chartUtils"
import type { Locale } from "@/lib/locale"
import { formatLabel, formatterFor, type ValueFormat } from "./valueFormats"

export type { ValueFormat } from "./valueFormats"

/** A monthly line chart on the design system: months on the x axis, one format for values. */
export function MetricLineChart({
  data,
  categories,
  colors,
  valueFormat,
  locale = "en",
  index = "month",
  showLegend,
  className,
}: {
  data: ChartDatum[]
  categories: string[]
  colors?: AvailableChartColorsKeys[]
  valueFormat: ValueFormat
  locale?: Locale
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
      valueFormatter={formatterFor(valueFormat, locale)}
      indexFormatter={(value) => formatLabel(value, locale)}
      // a single series needs no legend: the section title names it
      showLegend={showLegend ?? categories.length > 1}
      // Spanish money ticks ("US$300 mil") are wider than English ones ("$300k")
      yAxisWidth={valueFormat === "currency" && locale === "es" ? 88 : 64}
      className={className ?? "h-72"}
    />
  )
}
