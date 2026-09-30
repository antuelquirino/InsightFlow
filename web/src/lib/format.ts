// The only place in the app where numbers and dates become text, so every
// screen reads the same: $297k, $3.6M, 9.2%, 2.5x, Aug 2026.

const MISSING = "—"
const MINUS = "−" // same width as a digit, so tabular figures stay aligned

type Maybe = number | null | undefined

const isMissing = (value: Maybe): value is null | undefined =>
  value === null || value === undefined || Number.isNaN(value)

const fixed = (value: number, decimals: number) =>
  new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)

const sign = (value: number, signed: boolean) =>
  value < 0 ? MINUS : signed && value > 0 ? "+" : ""

/** $855 · $6.2k · $297k · $3.6M. Whole dollars below $1,000. */
export function formatCurrency(value: Maybe, { signed = false } = {}): string {
  if (isMissing(value)) return MISSING
  const abs = Math.abs(value)
  // Pick the unit from the rounded value, so 999,999 reads $1.0M, not $1,000k.
  const thousands = Number((abs / 1e3).toFixed(abs >= 1e4 ? 0 : 1))
  let body: string
  if (thousands >= 1000) body = `$${fixed(abs / 1e6, abs >= 9.95e6 ? 0 : 1)}M`
  else if (abs >= 1e3) body = `$${fixed(abs / 1e3, abs >= 1e4 ? 0 : 1)}k`
  else body = `$${fixed(abs, 0)}`
  return sign(value, signed) + body
}

/** Exact dollars with thousands separators, for tables: $297,287. */
export function formatCurrencyExact(value: Maybe): string {
  if (isMissing(value)) return MISSING
  return sign(value, false) + `$${fixed(Math.abs(value), 0)}`
}

/** 458 · 1,183 */
export function formatNumber(value: Maybe, decimals = 0): string {
  if (isMissing(value)) return MISSING
  return sign(value, false) + fixed(Math.abs(value), decimals)
}

/** A fraction as a percentage: 0.0918 -> 9.2% (1.239 -> 123.9%). */
export function formatPercent(
  fraction: Maybe,
  { decimals = 1, signed = false } = {},
): string {
  if (isMissing(fraction)) return MISSING
  return (
    sign(fraction, signed) + `${fixed(Math.abs(fraction) * 100, decimals)}%`
  )
}

/** A difference between two rates, in percentage points: 0.019 -> +1.9 pts. */
export function formatPoints(fraction: Maybe, { decimals = 1 } = {}): string {
  if (isMissing(fraction)) return MISSING
  return (
    sign(fraction, true) + `${fixed(Math.abs(fraction) * 100, decimals)} pts`
  )
}

/** 2.5x */
export function formatRatio(value: Maybe, decimals = 1): string {
  if (isMissing(value)) return MISSING
  return `${fixed(value, decimals)}x`
}

/** 6.4 months · 1 month */
export function formatMonths(value: Maybe, decimals = 1): string {
  if (isMissing(value)) return MISSING
  const text = fixed(value, decimals)
  return `${text} ${text === fixed(1, decimals) ? "month" : "months"}`
}

// The API sends months as "2026-08-01". Parse as UTC so no time zone can move
// the date to the previous day.
function toDate(iso: string): Date {
  const [year, month, day = 1] = iso.slice(0, 10).split("-").map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

/** "2026-08-01" -> Aug 2026 (short) · August 2026 (long) · Aug (month). */
export function formatMonth(
  iso: string | null | undefined,
  style: "short" | "long" | "month" = "short",
): string {
  if (!iso) return MISSING
  const options: Intl.DateTimeFormatOptions =
    style === "month"
      ? { month: "short", timeZone: "UTC" }
      : {
          month: style === "long" ? "long" : "short",
          year: "numeric",
          timeZone: "UTC",
        }
  return new Intl.DateTimeFormat("en-US", options).format(toDate(iso))
}

/** "2026-08-01" -> Aug 31, 2026: the last day of that month. */
export function formatMonthEnd(iso: string | null | undefined): string {
  if (!iso) return MISSING
  const start = toDate(iso)
  const end = new Date(
    Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0),
  )
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(end)
}

export type ChangeType = "relative" | "absolute"

/** A KPI change as the API sends it: relative -> +4.1%, absolute -> −1.3 pts. */
export function formatChange(change: Maybe, type: ChangeType): string {
  return type === "relative"
    ? formatPercent(change, { signed: true })
    : formatPoints(change)
}

export type Tone = "gain" | "loss" | "neutral"

/** Whether a change is good news: its direction times whether up is good. */
export function toneOf(change: Maybe, higherIsBetter: boolean): Tone {
  if (isMissing(change) || change === 0) return "neutral"
  return change > 0 === higherIsBetter ? "gain" : "loss"
}
