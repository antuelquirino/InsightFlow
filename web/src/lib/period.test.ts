import { describe, expect, it } from "vitest"

import { parsePeriod, periodRange } from "./period"

describe("period filter", () => {
  it("accepts only 6, 12 or 24 and defaults to 12", () => {
    expect(parsePeriod("6")).toBe(6)
    expect(parsePeriod("24")).toBe(24)
    expect(parsePeriod(["6", "24"])).toBe(6)
    expect(parsePeriod("7")).toBe(12)
    expect(parsePeriod(undefined)).toBe(12)
    expect(parsePeriod("abc")).toBe(12)
  })

  it("counts back from the latest month, inclusive", () => {
    expect(periodRange("2026-08-01", 12)).toEqual({
      start_month: "2025-09",
      end_month: "2026-08",
    })
    expect(periodRange("2026-08-01", 6)).toEqual({
      start_month: "2026-03",
      end_month: "2026-08",
    })
    expect(periodRange("2026-08-01", 24)).toEqual({
      start_month: "2024-09",
      end_month: "2026-08",
    })
  })

  it("crosses year boundaries", () => {
    expect(periodRange("2026-01-01", 6)).toEqual({
      start_month: "2025-08",
      end_month: "2026-01",
    })
  })
})
