import type { KpiItem } from "@/components/insight/KpiStrip"

import {
  formatChange,
  formatCurrency,
  formatMonth,
  formatNumber,
  formatPercent,
  previousMonth,
  toneOf,
} from "./format"
import { MESSAGES } from "./i18n"
import type { Locale } from "./locale"
import type { Kpi, SummaryResponse } from "./types"

/** The five headline KPIs of a month, as the dashboard shows them. */
export function headlineKpis(
  summary: SummaryResponse,
  locale: Locale = "en",
): KpiItem[] {
  const t = MESSAGES[locale].kpis
  const comparison = t.versus(
    formatMonth(previousMonth(summary.month), "month", { locale }),
  )
  const item = (label: string, kpi: Kpi, value: string): KpiItem => ({
    label,
    value,
    change: formatChange(kpi.change, kpi.change_type, { locale }),
    direction: !kpi.change ? "flat" : kpi.change > 0 ? "up" : "down",
    tone: toneOf(kpi.change, kpi.higher_is_better),
    comparison,
  })
  return [
    item(t.mrr, summary.mrr, formatCurrency(summary.mrr.value, { locale })),
    item(t.arr, summary.arr, formatCurrency(summary.arr.value, { locale })),
    item(
      t.nrr,
      summary.nrr,
      formatPercent(summary.nrr.value, { decimals: 0, locale }),
    ),
    item(
      t.logoChurn,
      summary.logo_churn_rate,
      formatPercent(summary.logo_churn_rate.value, { locale }),
    ),
    item(
      t.customers,
      summary.paying_customers,
      formatNumber(summary.paying_customers.value, { locale }),
    ),
  ]
}
