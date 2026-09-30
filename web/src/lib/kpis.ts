import type { KpiItem } from "@/components/insight/KpiStrip"

import {
  formatChange,
  formatCurrency,
  formatMonth,
  formatNumber,
  formatPercent,
  toneOf,
} from "./format"
import type { Kpi, SummaryResponse } from "./types"

function item(
  label: string,
  kpi: Kpi,
  value: string,
  previousMonth: string,
): KpiItem {
  const change = kpi.change
  return {
    label,
    value,
    change: formatChange(change, kpi.change_type),
    direction: !change ? "flat" : change > 0 ? "up" : "down",
    tone: toneOf(change, kpi.higher_is_better),
    comparison: `vs ${previousMonth}`,
  }
}

/** The five headline KPIs of a month, as the Overview shows them. */
export function headlineKpis(summary: SummaryResponse): KpiItem[] {
  const [year, month] = summary.month.split("-").map(Number)
  const previous = new Date(Date.UTC(year, month - 2, 1)).toISOString()
  const previousMonth = formatMonth(previous, "month")
  return [
    item("MRR", summary.mrr, formatCurrency(summary.mrr.value), previousMonth),
    item("ARR", summary.arr, formatCurrency(summary.arr.value), previousMonth),
    item(
      "Net revenue retention",
      summary.nrr,
      formatPercent(summary.nrr.value, { decimals: 0 }),
      previousMonth,
    ),
    item(
      "Logo churn",
      summary.logo_churn_rate,
      formatPercent(summary.logo_churn_rate.value),
      previousMonth,
    ),
    item(
      "Paying customers",
      summary.paying_customers,
      formatNumber(summary.paying_customers.value),
      previousMonth,
    ),
  ]
}
