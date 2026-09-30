import { CHANNEL_LABELS, PLAN_LABELS } from "@/lib/entities"
import {
  formatCurrency,
  formatMonth,
  formatMonths,
  formatNumber,
  formatPercent,
  formatRatio,
} from "@/lib/format"
import { MESSAGES } from "@/lib/i18n"
import type { Locale } from "@/lib/locale"

// Server components cannot pass functions to client components, so charts
// receive the name of a format (and the language) and look the formatter up here.
export type ValueFormat = "currency" | "percent" | "number" | "ratio" | "months"

export function formatterFor(
  format: ValueFormat,
  locale: Locale = "en",
): (value: number) => string {
  switch (format) {
    case "currency":
      return (value) => formatCurrency(value, { locale })
    case "percent":
      return (value) => formatPercent(value, { locale })
    case "ratio":
      return (value) => formatRatio(value, { locale })
    case "months":
      return (value) => formatMonths(value, { locale })
    case "number":
      return (value) =>
        formatNumber(value, {
          decimals: Number.isInteger(value) ? 0 : 1,
          locale,
        })
  }
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export const isIsoDate = (value: unknown): value is string =>
  typeof value === "string" && ISO_DATE.test(value)

/** A category label: ISO months become "Aug 2026", plan and channel ids their names. */
export function formatLabel(value: unknown, locale: Locale = "en"): string {
  if (isIsoDate(value)) return formatMonth(value, "short", { locale })
  const text = String(value ?? "")
  const channels: Record<string, string> =
    locale === "en" ? CHANNEL_LABELS : MESSAGES[locale].channels.names
  const plans: Record<string, string> = PLAN_LABELS
  return plans[text] ?? channels[text] ?? text
}

/**
 * The agent returns arbitrary columns; guess how to show a column's numbers
 * from its name (ltv_to_cac -> ratio, *_rate -> percent, mrr -> currency).
 */
export function guessFormat(column: string): ValueFormat {
  const name = column.toLowerCase()
  if (/to_cac|ratio|multiple/.test(name)) return "ratio"
  if (/payback|months_to/.test(name)) return "months"
  // rate words first: gross_mrr_churn_rate is a rate even though it says mrr
  if (/rate|retention|nrr|share|pct|percent|trend/.test(name)) return "percent"
  if (/mrr|arr|revenue|cac|ltv|arpa|spend|amount|price/.test(name))
    return "currency"
  return "number"
}
