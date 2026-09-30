// The global period filter: the last 6, 12 or 24 months of data, kept in the
// URL (?period=12) so a link always opens on the same view.

export const PERIODS = [6, 12, 24] as const
export type Period = (typeof PERIODS)[number]
export const DEFAULT_PERIOD: Period = 12

export function parsePeriod(value: string | string[] | undefined): Period {
  const number = Number(Array.isArray(value) ? value[0] : value)
  return (PERIODS as readonly number[]).includes(number)
    ? (number as Period)
    : DEFAULT_PERIOD
}

/** "2026-08-01" and 12 -> { start_month: "2025-09", end_month: "2026-08" } */
export function periodRange(latestMonth: string, period: Period) {
  const [year, month] = latestMonth.split("-").map(Number)
  const start = new Date(Date.UTC(year, month - 1 - (period - 1), 1))
  const yyyyMm = (date: Date) =>
    `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`
  return {
    start_month: yyyyMm(start),
    end_month: yyyyMm(new Date(Date.UTC(year, month - 1, 1))),
  }
}
