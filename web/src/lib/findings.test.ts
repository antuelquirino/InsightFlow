import { describe, expect, it } from "vitest"

import { mrrLeadFinding } from "./findings"
import type { Kpi, SummaryResponse } from "./types"

const kpi = (value: number, change: number): Kpi => ({
  value,
  previous_value: null,
  change,
  change_type: "relative",
  higher_is_better: true,
})

const SUMMARY = {
  month: "2026-08-01",
  mrr: kpi(297287, 0.0406),
} as SummaryResponse

describe("lead finding", () => {
  it("reads naturally in English", () => {
    const lead = mrrLeadFinding(SUMMARY)
    expect(`${lead.before}[${lead.mark}]${lead.after}`).toBe(
      "MRR reached [$297k] in August 2026, up 4.1% on July.",
    )
  })

  it("reads naturally in Spanish", () => {
    const lead = mrrLeadFinding(SUMMARY, "es")
    expect(`${lead.before}[${lead.mark}]${lead.after}`).toBe(
      "El MRR llegó a [US$297 mil] en agosto de 2026, 4,1% más que en julio.",
    )
  })

  it("says down when MRR fell", () => {
    const lead = mrrLeadFinding({ ...SUMMARY, mrr: kpi(290000, -0.02) }, "es")
    expect(lead.after).toBe(" en agosto de 2026, 2,0% menos que en julio.")
  })
})
