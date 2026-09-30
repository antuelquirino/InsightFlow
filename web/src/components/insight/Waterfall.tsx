"use client"

// The MRR bridge as a waterfall: last month's MRR, each movement stacked on
// the running total, this month's MRR. Start and end are neutral; movements
// are gain or loss because here the color does mean "improves" / "worsens".
// Movements are small next to the total, so the value axis does not start at
// zero; the section's caption says so.

import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts"

import { useSyncExternalStore } from "react"

import { formatCurrency } from "@/lib/format"
import type { Locale } from "@/lib/locale"

// Seven full labels do not fit under the bars on a phone.
const NARROW = "(max-width: 640px)"
const subscribe = (onChange: () => void) => {
  const query = window.matchMedia(NARROW)
  query.addEventListener("change", onChange)
  return () => query.removeEventListener("change", onChange)
}
const useNarrow = () =>
  useSyncExternalStore(
    subscribe,
    () => window.matchMedia(NARROW).matches,
    () => false,
  )

export interface WaterfallStep {
  label: string
  shortLabel: string // used on narrow screens
  value: number // the movement, or the total for start/end
  kind: "total" | "movement"
}

interface Bar {
  label: string
  base: number
  size: number
  value: number
  kind: WaterfallStep["kind"]
  text: string // the figure above the bar: totals plain, movements signed
}

function toBars(steps: WaterfallStep[], locale: Locale): Bar[] {
  let running = 0
  return steps.map((step) => {
    if (step.kind === "total") {
      running = step.value
      return {
        label: step.label,
        base: 0,
        size: step.value,
        value: step.value,
        kind: step.kind,
        text: formatCurrency(step.value, { locale }),
      }
    }
    const from = running
    running += step.value
    return {
      label: step.label,
      base: Math.min(from, running),
      size: Math.abs(step.value),
      value: step.value,
      kind: step.kind,
      text: formatCurrency(step.value, { signed: true, locale }),
    }
  })
}

const fillFor = (bar: Bar) =>
  bar.kind === "total"
    ? "var(--series-muted)"
    : bar.value >= 0
      ? "var(--gain)"
      : "var(--loss)"

export function Waterfall({
  steps,
  axisFloor,
  locale = "en",
}: {
  steps: WaterfallStep[]
  locale?: Locale
  /** Where the value axis starts; below the smallest running total. */
  axisFloor: number
}) {
  const narrow = useNarrow()
  const bars = toBars(
    narrow ? steps.map((step) => ({ ...step, label: step.shortLabel })) : steps,
    locale,
  )
  const top = Math.max(...bars.map((bar) => bar.base + bar.size))
  return (
    <div className="h-72">
      <ResponsiveContainer>
        <BarChart
          data={bars}
          margin={{ top: 24, right: 0, bottom: 0, left: 0 }}
          barCategoryGap="22%"
        >
          <XAxis
            dataKey="label"
            axisLine={{ stroke: "var(--rule)" }}
            tickLine={false}
            interval={0}
            tick={{ fill: "var(--graphite)", fontSize: 12 }}
          />
          <YAxis hide domain={[axisFloor, top * 1.02]} allowDataOverflow />
          {/* invisible spacer up to where each movement starts */}
          <Bar
            dataKey="base"
            stackId="bridge"
            fill="transparent"
            isAnimationActive={false}
          />
          <Bar
            dataKey="size"
            stackId="bridge"
            radius={[4, 4, 0, 0]}
            isAnimationActive={false}
          >
            {bars.map((bar) => (
              <Cell key={bar.label} fill={fillFor(bar)} />
            ))}
            <LabelList
              dataKey="text"
              position="top"
              offset={6}
              style={{
                fill: "var(--ink)",
                fontSize: 12,
                fontVariantNumeric: "tabular-nums",
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
