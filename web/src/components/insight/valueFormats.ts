import {
  formatCurrency,
  formatMonth,
  formatMonths,
  formatNumber,
  formatPercent,
  formatRatio,
} from "@/lib/format"
import { CHANNEL_LABELS, PLAN_LABELS } from "@/lib/entities"

// Server components cannot pass functions to client components, so charts
// receive the name of a format and look the formatter up here.
export type ValueFormat = "currency" | "percent" | "number" | "ratio" | "months"

export const VALUE_FORMATTERS: Record<ValueFormat, (value: number) => string> =
  {
    currency: (value) => formatCurrency(value),
    percent: (value) => formatPercent(value),
    number: (value) => formatNumber(value, Number.isInteger(value) ? 0 : 1),
    ratio: (value) => formatRatio(value),
    months: (value) => formatMonths(value),
  }

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export const isIsoDate = (value: unknown): value is string =>
  typeof value === "string" && ISO_DATE.test(value)

const ENTITY_LABELS: Record<string, string> = {
  ...PLAN_LABELS,
  ...CHANNEL_LABELS,
}

/** A category label: ISO months become "Aug 2026", plan and channel ids their names. */
export const formatLabel = (value: unknown): string => {
  if (isIsoDate(value)) return formatMonth(value)
  const text = String(value ?? "")
  return ENTITY_LABELS[text] ?? text
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
