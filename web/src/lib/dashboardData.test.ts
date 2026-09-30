import { describe, expect, it } from "vitest"

import {
  bridgeAxisFloor,
  bridgeFinding,
  bridgeSteps,
  channelReturns,
  largestPlanFinding,
  mrrByPlanRows,
  mrrTrendFinding,
  starterPeakFinding,
  starterVsOthers,
} from "./dashboardData"
import type { ChurnPoint, MrrMovementsMonth, MrrPoint } from "./types"

const AUGUST: MrrMovementsMonth = {
  month: "2026-08-01",
  starting_mrr: 285694,
  new_mrr: 10284,
  expansion_mrr: 6217,
  contraction_mrr: -294,
  churned_mrr: -5160,
  reactivation_mrr: 546,
  net_new_mrr: 11593,
  ending_mrr: 297287,
  new_customers: 33,
  churned_customers: 19,
  reactivated_customers: 1,
}

const churn = (
  month: string,
  group: string,
  atStart: number,
  churned: number,
): ChurnPoint => ({
  month,
  group,
  customers_at_start: atStart,
  churned_customers: churned,
  logo_churn_rate: churned / atStart,
  revenue_churn_rate: null,
  gross_mrr_churn_rate: null,
  net_mrr_churn_rate: null,
})

describe("MRR bridge", () => {
  it("steps from last month to this month", () => {
    const steps = bridgeSteps(AUGUST)
    expect(steps.map((s) => s.label)).toEqual([
      "Last month",
      "New",
      "Expansion",
      "Contraction",
      "Churn",
      "Reactivation",
      "This month",
    ])
    const movements = steps
      .filter((s) => s.kind === "movement")
      .reduce((sum, s) => sum + s.value, 0)
    expect(AUGUST.starting_mrr + movements).toBe(AUGUST.ending_mrr)
  })

  it("starts the axis below the lowest point, at a round number", () => {
    const floor = bridgeAxisFloor(AUGUST)
    expect(floor).toBeLessThan(AUGUST.starting_mrr)
    expect(floor % 1000).toBe(0)
    expect(floor).toBeGreaterThan(200000) // movements stay visible
  })

  it("says which side won", () => {
    expect(bridgeFinding(AUGUST)).toBe(
      "Expansion outweighed churn in August 2026",
    )
    expect(bridgeFinding({ ...AUGUST, churned_mrr: -9000 })).toBe(
      "Churn outweighed expansion in August 2026",
    )
  })
})

describe("plans", () => {
  const series: MrrPoint[] = [
    {
      month: "2026-07-01",
      group: "starter",
      mrr: 100,
      arr: 1200,
      paying_customers: 5,
    },
    {
      month: "2026-08-01",
      group: "starter",
      mrr: 100,
      arr: 1200,
      paying_customers: 5,
    },
    {
      month: "2026-08-01",
      group: "enterprise",
      mrr: 300,
      arr: 3600,
      paying_customers: 1,
    },
  ]

  it("pivots to one column per plan, zero when a plan has no customers", () => {
    expect(mrrByPlanRows(series)).toEqual([
      { month: "2026-07-01", Starter: 100, Pro: 0, Enterprise: 0 },
      { month: "2026-08-01", Starter: 100, Pro: 0, Enterprise: 300 },
    ])
  })

  it("names the largest plan's share", () => {
    expect(largestPlanFinding(mrrByPlanRows(series))).toBe(
      "Enterprise brings 75% of MRR",
    )
  })

  it("compares Starter churn with the other plans combined", () => {
    const rows = starterVsOthers([
      churn("2026-01-01", "starter", 100, 12),
      churn("2026-01-01", "pro", 60, 1),
      churn("2026-01-01", "enterprise", 40, 1),
    ])
    expect(rows).toEqual([
      { month: "2026-01-01", Starter: 0.12, "Other plans": 0.02 },
    ])
    expect(starterPeakFinding(rows)).toBe(
      "Starter churn peaked at 12.0% in January 2026",
    )
  })
})

describe("trend and channels", () => {
  it("describes the MRR trend", () => {
    const point = (month: string, mrr: number): MrrPoint => ({
      month,
      group: "total",
      mrr,
      arr: mrr * 12,
      paying_customers: 1,
    })
    expect(
      mrrTrendFinding([
        point("2025-09-01", 134607),
        point("2026-08-01", 297287),
      ]),
    ).toBe("MRR grew from $135k to $297k")
  })

  it("ranks channels and names the weakest", () => {
    const channel = (
      acquisition_channel: "organic" | "paid_ads",
      ltv_to_cac: number,
    ) => ({
      acquisition_channel,
      spend_12m: 1,
      new_customers_12m: 1,
      cac: 1,
      arpa: 1,
      monthly_logo_churn_rate: 0.01,
      ltv: 1,
      ltv_to_cac,
      payback_months: 1,
    })
    const result = channelReturns([
      channel("paid_ads", 2.4964),
      channel("organic", 21.5),
    ])
    expect(result.rows.map((r) => r.channel)).toEqual(["Organic", "Paid ads"])
    expect(result.finding).toBe(
      "Paid ads returns the least: a customer is worth 2.5x what it cost",
    )
  })
})
