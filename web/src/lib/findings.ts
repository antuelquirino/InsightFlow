// Findings are sentences built from API data, never written by a model: the
// words are templates, every number comes from the response.

import { formatCurrency, formatMonth, formatPercent } from "./format"
import type { SummaryResponse } from "./types"

export interface MarkedSentence {
  before: string
  mark: string // the key figure, shown with the marker stroke
  after: string
}

/** "MRR reached [$297k] in August 2026, up 4.1% on July." */
export function mrrLeadFinding(summary: SummaryResponse): MarkedSentence {
  const { value, change } = summary.mrr
  const month = formatMonth(summary.month, "long")
  const [year, monthNumber] = summary.month.split("-").map(Number)
  const previous = formatMonth(
    new Date(Date.UTC(year, monthNumber - 2, 1)).toISOString(),
    "long",
  ).split(" ")[0]
  let movement = ""
  if (change !== null && change !== 0) {
    const direction = change > 0 ? "up" : "down"
    movement = `, ${direction} ${formatPercent(Math.abs(change))} on ${previous}`
  }
  return {
    before: "MRR reached ",
    mark: formatCurrency(value),
    after: ` in ${month}${movement}.`,
  }
}
