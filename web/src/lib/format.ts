// The only place in the app where numbers and dates become text, so every
// screen reads the same: $297k, $3.6M, 9.2%, 2.5x, Aug 2026 in English, and
// US$297 mil, US$3,6 M, 9,2%, 2,5x, ago 2026 in Spanish (Argentina).

import { INTL_LOCALES, type Locale } from "./locale"

const MISSING = "—"
const MINUS = "−" // same width as a digit, so tabular figures stay aligned

type Maybe = number | null | undefined

interface Options {
  locale?: Locale
}

const isMissing = (value: Maybe): value is null | undefined =>
  value === null || value === undefined || Number.isNaN(value)

const fixed = (value: number, decimals: number, locale: Locale = "en") =>
  new Intl.NumberFormat(INTL_LOCALES[locale], {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)

const sign = (value: number, signed: boolean) =>
  value < 0 ? MINUS : signed && value > 0 ? "+" : ""

// How each language writes money: prefix and the thousand / million units.
const CURRENCY = {
  en: { prefix: "$", thousand: "k", million: "M" },
  es: { prefix: "US$", thousand: " mil", million: " M" },
} as const

/** $855 · $6.2k · $297k · $3.6M (es: US$855 · US$6,2 mil · US$297 mil · US$3,6 M). */
export function formatCurrency(
  value: Maybe,
  { signed = false, locale = "en" }: Options & { signed?: boolean } = {},
): string {
  if (isMissing(value)) return MISSING
  const unit = CURRENCY[locale]
  const abs = Math.abs(value)
  // Pick the unit from the rounded value, so 999,999 reads $1.0M, not $1,000k.
  const thousands = Number((abs / 1e3).toFixed(abs >= 1e4 ? 0 : 1))
  let body: string
  if (thousands >= 1000)
    body = `${fixed(abs / 1e6, abs >= 9.95e6 ? 0 : 1, locale)}${unit.million}`
  else if (abs >= 1e3)
    body = `${fixed(abs / 1e3, abs >= 1e4 ? 0 : 1, locale)}${unit.thousand}`
  else body = fixed(abs, 0, locale)
  return sign(value, signed) + unit.prefix + body
}

/** Exact dollars with thousands separators, for tables: $297,287 (es: US$297.287). */
export function formatCurrencyExact(
  value: Maybe,
  { locale = "en" }: Options = {},
): string {
  if (isMissing(value)) return MISSING
  return (
    sign(value, false) +
    CURRENCY[locale].prefix +
    fixed(Math.abs(value), 0, locale)
  )
}

/** 458 · 1,183 (es: 1.183) */
export function formatNumber(
  value: Maybe,
  { decimals = 0, locale = "en" }: Options & { decimals?: number } = {},
): string {
  if (isMissing(value)) return MISSING
  return sign(value, false) + fixed(Math.abs(value), decimals, locale)
}

/** A fraction as a percentage: 0.0918 -> 9.2% (es: 9,2%). */
export function formatPercent(
  fraction: Maybe,
  {
    decimals = 1,
    signed = false,
    locale = "en",
  }: Options & { decimals?: number; signed?: boolean } = {},
): string {
  if (isMissing(fraction)) return MISSING
  return (
    sign(fraction, signed) +
    `${fixed(Math.abs(fraction) * 100, decimals, locale)}%`
  )
}

/** A difference between two rates, in percentage points: +1.9 pts (es: +1,9 pp). */
export function formatPoints(
  fraction: Maybe,
  { decimals = 1, locale = "en" }: Options & { decimals?: number } = {},
): string {
  if (isMissing(fraction)) return MISSING
  const unit = locale === "es" ? "pp" : "pts"
  return (
    sign(fraction, true) +
    `${fixed(Math.abs(fraction) * 100, decimals, locale)} ${unit}`
  )
}

/** 2.5x (es: 2,5x) */
export function formatRatio(
  value: Maybe,
  { decimals = 1, locale = "en" }: Options & { decimals?: number } = {},
): string {
  if (isMissing(value)) return MISSING
  return `${fixed(value, decimals, locale)}x`
}

/** 6.4 months · 1.0 month (es: 6,4 meses · 1,0 mes) */
export function formatMonths(
  value: Maybe,
  { decimals = 1, locale = "en" }: Options & { decimals?: number } = {},
): string {
  if (isMissing(value)) return MISSING
  const text = fixed(value, decimals, locale)
  const one = text === fixed(1, decimals, locale)
  const word =
    locale === "es" ? (one ? "mes" : "meses") : one ? "month" : "months"
  return `${text} ${word}`
}

// The API sends months as "2026-08-01". Parse as UTC so no time zone can move
// the date to the previous day.
function toDate(iso: string): Date {
  const [year, month, day = 1] = iso.slice(0, 10).split("-").map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

/**
 * "2026-08-01" -> Aug 2026 (short) · August 2026 (long) · Aug (month) · August (monthLong).
 * Spanish: ago 2026 · agosto de 2026 · ago · agosto.
 */
export function formatMonth(
  iso: string | null | undefined,
  style: "short" | "long" | "month" | "monthLong" = "short",
  { locale = "en" }: Options = {},
): string {
  if (!iso) return MISSING
  const options: Intl.DateTimeFormatOptions = {
    month: style === "long" || style === "monthLong" ? "long" : "short",
    year: style === "short" || style === "long" ? "numeric" : undefined,
    timeZone: "UTC",
  }
  return new Intl.DateTimeFormat(INTL_LOCALES[locale], options).format(
    toDate(iso),
  )
}

/** "2026-08-01" -> Aug 31, 2026 (es: 31 de ago de 2026): the last day of that month. */
export function formatMonthEnd(
  iso: string | null | undefined,
  { locale = "en" }: Options = {},
): string {
  if (!iso) return MISSING
  const start = toDate(iso)
  const end = new Date(
    Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0),
  )
  return new Intl.DateTimeFormat(INTL_LOCALES[locale], {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(end)
}

/** "2026-08-01" -> "2026-07-01": the month before. */
export function previousMonth(iso: string): string {
  const [year, month] = iso.split("-").map(Number)
  return new Date(Date.UTC(year, month - 2, 1)).toISOString().slice(0, 10)
}

export type ChangeType = "relative" | "absolute"

/** A KPI change as the API sends it: relative -> +4.1%, absolute -> −1.3 pts. */
export function formatChange(
  change: Maybe,
  type: ChangeType,
  { locale = "en" }: Options = {},
): string {
  return type === "relative"
    ? formatPercent(change, { signed: true, locale })
    : formatPoints(change, { locale })
}

export type Tone = "gain" | "loss" | "neutral"

/** Whether a change is good news: its direction times whether up is good. */
export function toneOf(change: Maybe, higherIsBetter: boolean): Tone {
  if (isMissing(change) || change === 0) return "neutral"
  return change > 0 === higherIsBetter ? "gain" : "loss"
}
