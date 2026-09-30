// Findings are sentences built from API data, never written by a model: the
// words are templates (lib/i18n.ts), every number comes from the response.

import {
  formatCurrency,
  formatMonth,
  formatPercent,
  previousMonth,
} from "./format"
import { MESSAGES } from "./i18n"
import type { Locale } from "./locale"
import type { SummaryResponse } from "./types"

export interface MarkedSentence {
  before: string
  mark: string // the key figure, shown with the marker stroke
  after: string
}

/** "MRR reached [$297k] in August 2026, up 4.1% on July." */
export function mrrLeadFinding(
  summary: SummaryResponse,
  locale: Locale = "en",
): MarkedSentence {
  const t = MESSAGES[locale].summary
  const { value, change } = summary.mrr
  const [before, after] = t.lead(formatMonth(summary.month, "long", { locale }))
  let movement = ""
  if (change !== null && change !== 0) {
    movement = t.leadChange(
      change > 0 ? "up" : "down",
      formatPercent(Math.abs(change), { locale }),
      formatMonth(previousMonth(summary.month), "monthLong", { locale }),
    )
  }
  return {
    before,
    mark: formatCurrency(value, { locale }),
    after: `${after}${movement}.`,
  }
}
