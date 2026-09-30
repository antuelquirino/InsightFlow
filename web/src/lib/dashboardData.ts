// Pure transformations from API responses to what the dashboard draws, plus
// the finding sentences. Every number comes from the API; these functions only
// reshape, combine and pick. Words come from lib/i18n.ts.

import type { WaterfallStep } from "@/components/insight/Waterfall"
import type { ChartDatum } from "./chartUtils"
import { PLAN_LABELS, PLANS } from "./entities"
import {
  formatCurrency,
  formatMonth,
  formatPercent,
  formatRatio,
} from "./format"
import { MESSAGES, type BridgeStep } from "./i18n"
import type { Locale } from "./locale"
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
export function largestPlanFinding(
  rows: ChartDatum[],
  locale: Locale = "en",
): string {
  const t = MESSAGES[locale].byPlan
  const last = rows[rows.length - 1]
  if (!last) return t.fallback
  const totals = PLANS.map((plan) => ({
    label: PLAN_LABELS[plan],
    mrr: Number(last[PLAN_LABELS[plan]] ?? 0),
  }))
  const total = totals.reduce((sum, plan) => sum + plan.mrr, 0)
  if (!total) return t.fallback
  const largest = totals.reduce((best, plan) =>
    plan.mrr > best.mrr ? plan : best,
  )
  return t.finding(
    largest.label,
    formatPercent(largest.mrr / total, { decimals: 0, locale }),
  )
}

/** Starter's churn against all other plans combined, month by month. */
export function starterVsOthers(
  series: ChurnPoint[],
  locale: Locale = "en",
): ChartDatum[] {
  const otherPlans = MESSAGES[locale].churn.otherPlans
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
      [otherPlans]: atStart ? churned / atStart : null,
    }
  })
}

/** "Starter churn peaked at 12.4% in January 2026". */
export function starterPeakFinding(
  rows: ChartDatum[],
  locale: Locale = "en",
): string {
  const t = MESSAGES[locale].churn
  const withValues = rows.filter((row) => typeof row.Starter === "number")
  if (!withValues.length) return t.fallback
  const peak = withValues.reduce((best, row) =>
    Number(row.Starter) > Number(best.Starter) ? row : best,
  )
  return t.finding(
    formatPercent(Number(peak.Starter), { locale }),
    formatMonth(String(peak.month), "long", { locale }),
  )
}

/** "MRR grew from $135k to $297k" over the rows shown. */
export function mrrTrendFinding(
  series: MrrPoint[],
  locale: Locale = "en",
): string {
  const t = MESSAGES[locale].mrrTrend
  if (series.length < 2) return t.fallback
  const first = series[0].mrr
  const last = series[series.length - 1].mrr
  return t.finding(
    last >= first ? "grew" : "fell",
    formatCurrency(first, { locale }),
    formatCurrency(last, { locale }),
  )
}

/** The waterfall of one month: start, every movement, end. */
export function bridgeSteps(
  month: MrrMovementsMonth,
  locale: Locale = "en",
): WaterfallStep[] {
  const steps = MESSAGES[locale].bridge.steps
  const step = (
    key: BridgeStep,
    value: number,
    kind: WaterfallStep["kind"],
  ): WaterfallStep => ({
    label: steps[key].label,
    shortLabel: steps[key].short,
    value,
    kind,
  })
  return [
    step("lastMonth", month.starting_mrr, "total"),
    step("new", month.new_mrr, "movement"),
    step("expansion", month.expansion_mrr, "movement"),
    step("contraction", month.contraction_mrr, "movement"),
    step("churn", month.churned_mrr, "movement"),
    step("reactivation", month.reactivation_mrr, "movement"),
    step("thisMonth", month.ending_mrr, "total"),
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
  const unit = 10 ** Math.floor(Math.log10(Math.max(lowest, 1)) - 1)
  return Math.max(0, Math.floor((lowest - span * 1.5) / unit) * unit)
}

/** "Expansion outweighed churn in August 2026", or the other way round. */
export function bridgeFinding(
  month: MrrMovementsMonth,
  locale: Locale = "en",
): string {
  return MESSAGES[locale].bridge.finding(
    month.expansion_mrr >= Math.abs(month.churned_mrr) ? "expansion" : "churn",
    formatMonth(month.month, "long", { locale }),
  )
}

/** Channels by return per dollar, best first, with the weakest one called out. */
export function channelReturns(
  channels: ChannelEconomics[],
  locale: Locale = "en",
) {
  const t = MESSAGES[locale].channels
  const ranked = channels
    .filter((channel) => channel.ltv_to_cac !== null)
    .sort((a, b) => Number(b.ltv_to_cac) - Number(a.ltv_to_cac))
  const weakest = ranked[ranked.length - 1]
  return {
    series: t.series,
    rows: ranked.map((channel) => ({
      channel: t.names[channel.acquisition_channel],
      [t.series]: channel.ltv_to_cac,
    })) as ChartDatum[],
    weakest,
    finding: weakest
      ? t.finding(
          t.names[weakest.acquisition_channel],
          formatRatio(weakest.ltv_to_cac, { locale }),
        )
      : t.fallback,
  }
}
