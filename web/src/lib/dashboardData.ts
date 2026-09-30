// Pure transformations from API responses to what the dashboard draws, plus
// the finding sentences. Every number comes from the API; these functions only
// reshape, combine and pick.

import type { WaterfallStep } from "@/components/insight/Waterfall"
import type { ChartDatum } from "./chartUtils"
import { CHANNEL_LABELS, PLAN_LABELS, PLANS } from "./entities"
import {
  formatCurrency,
  formatMonth,
  formatPercent,
  formatRatio,
} from "./format"
import type {
  ChannelEconomics,
  ChurnPoint,
  MrrMovementsMonth,
  MrrPoint,
} from "./types"

/** One row per month with one column per plan: { month, Starter, Pro, Enterprise }. */
export function mrrByPlanRows(series: MrrPoint[]): ChartDatum[] {
  const months = [...new Set(series.map((point) => point.month))].sort()
  return months.map((month) => {
    const row: ChartDatum = { month }
    for (const plan of PLANS) {
      const point = series.find((p) => p.month === month && p.group === plan)
      row[PLAN_LABELS[plan]] = point?.mrr ?? 0
    }
    return row
  })
}

/** "Enterprise brings 76% of MRR": the largest plan's share in the last month. */
export function largestPlanFinding(rows: ChartDatum[]): string {
  const last = rows[rows.length - 1]
  if (!last) return "MRR by plan"
  const totals = PLANS.map((plan) => ({
    label: PLAN_LABELS[plan],
    mrr: Number(last[PLAN_LABELS[plan]] ?? 0),
  }))
  const total = totals.reduce((sum, plan) => sum + plan.mrr, 0)
  const largest = totals.reduce((best, plan) =>
    plan.mrr > best.mrr ? plan : best,
  )
  if (!total) return "MRR by plan"
  return `${largest.label} brings ${formatPercent(largest.mrr / total, { decimals: 0 })} of MRR`
}

/** Starter's churn against all other plans combined, month by month. */
export function starterVsOthers(series: ChurnPoint[]): ChartDatum[] {
  const months = [...new Set(series.map((point) => point.month))].sort()
  return months.map((month) => {
    const rows = series.filter((point) => point.month === month)
    const starter = rows.find((point) => point.group === "starter")
    const others = rows.filter((point) => point.group !== "starter")
    const atStart = others.reduce((sum, p) => sum + p.customers_at_start, 0)
    const churned = others.reduce((sum, p) => sum + p.churned_customers, 0)
    return {
      month,
      Starter: starter?.logo_churn_rate ?? null,
      "Other plans": atStart ? churned / atStart : null,
    }
  })
}

/** "Starter churn peaked at 12.4% in January 2026". */
export function starterPeakFinding(rows: ChartDatum[]): string {
  const withValues = rows.filter((row) => typeof row.Starter === "number")
  if (!withValues.length) return "Starter churn"
  const peak = withValues.reduce((best, row) =>
    Number(row.Starter) > Number(best.Starter) ? row : best,
  )
  return `Starter churn peaked at ${formatPercent(Number(peak.Starter))} in ${formatMonth(String(peak.month), "long")}`
}

/** "MRR grew from $135k to $297k" over the rows shown. */
export function mrrTrendFinding(series: MrrPoint[]): string {
  if (series.length < 2) return "Monthly recurring revenue"
  const first = series[0].mrr
  const last = series[series.length - 1].mrr
  const verb = last >= first ? "grew" : "fell"
  return `MRR ${verb} from ${formatCurrency(first)} to ${formatCurrency(last)}`
}

const step = (
  label: string,
  shortLabel: string,
  value: number,
  kind: WaterfallStep["kind"],
): WaterfallStep => ({ label, shortLabel, value, kind })

/** The waterfall of one month: start, every movement, end. */
export function bridgeSteps(month: MrrMovementsMonth): WaterfallStep[] {
  return [
    step("Last month", "Start", month.starting_mrr, "total"),
    step("New", "New", month.new_mrr, "movement"),
    step("Expansion", "Exp.", month.expansion_mrr, "movement"),
    step("Contraction", "Contr.", month.contraction_mrr, "movement"),
    step("Churn", "Churn", month.churned_mrr, "movement"),
    step("Reactivation", "React.", month.reactivation_mrr, "movement"),
    step("This month", "End", month.ending_mrr, "total"),
  ]
}

/** Where the waterfall's axis starts: a round number below the lowest point. */
export function bridgeAxisFloor(month: MrrMovementsMonth): number {
  let running = month.starting_mrr
  let lowest = running
  for (const step of bridgeSteps(month).slice(1, -1)) {
    running += step.value
    lowest = Math.min(lowest, running)
  }
  const span = Math.max(month.starting_mrr, month.ending_mrr) - lowest
  const step = 10 ** Math.floor(Math.log10(Math.max(lowest, 1)) - 1)
  return Math.max(0, Math.floor((lowest - span * 1.5) / step) * step)
}

/** "Expansion outweighed churn in August 2026", or the other way round. */
export function bridgeFinding(month: MrrMovementsMonth): string {
  const growth = month.expansion_mrr
  const losses = Math.abs(month.churned_mrr)
  const when = formatMonth(month.month, "long")
  return growth >= losses
    ? `Expansion outweighed churn in ${when}`
    : `Churn outweighed expansion in ${when}`
}

/** Channels by return per dollar, best first, with the weakest one called out. */
export function channelReturns(channels: ChannelEconomics[]) {
  const ranked = channels
    .filter((channel) => channel.ltv_to_cac !== null)
    .sort((a, b) => Number(b.ltv_to_cac) - Number(a.ltv_to_cac))
  const weakest = ranked[ranked.length - 1]
  return {
    rows: ranked.map((channel) => ({
      channel: CHANNEL_LABELS[channel.acquisition_channel],
      "LTV to CAC": channel.ltv_to_cac,
    })) as ChartDatum[],
    weakest,
    finding: weakest
      ? `${CHANNEL_LABELS[weakest.acquisition_channel]} returns the least: a customer is worth ${formatRatio(weakest.ltv_to_cac)} what it cost`
      : "Return on acquisition by channel",
  }
}
