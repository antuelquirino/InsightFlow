import { describe, expect, it } from "vitest"

import { formatLabel, guessFormat } from "@/components/insight/valueFormats"

import {
  formatChange,
  formatCurrency,
  formatCurrencyExact,
  formatMonth,
  formatMonthEnd,
  formatMonths,
  formatNumber,
  formatPercent,
  formatPoints,
  formatRatio,
  toneOf,
} from "./format"

const MINUS = "−"

describe("formatCurrency", () => {
  it.each([
    [855.37, "$855"],
    [6217, "$6.2k"],
    [297287, "$297k"],
    [3567444, "$3.6M"],
    [36991946, "$37M"],
    [999999, "$1.0M"],
    [0, "$0"],
  ])("%d -> %s", (value, expected) => {
    expect(formatCurrency(value)).toBe(expected)
  })

  it("uses a typographic minus and optional plus", () => {
    expect(formatCurrency(-5160)).toBe(`${MINUS}$5.2k`)
    expect(formatCurrency(10284, { signed: true })).toBe("+$10k")
  })

  it("shows a dash for missing values", () => {
    expect(formatCurrency(null)).toBe("—")
    expect(formatCurrency(undefined)).toBe("—")
    expect(formatCurrency(Number.NaN)).toBe("—")
  })

  it("exact dollars for tables", () => {
    expect(formatCurrencyExact(297287)).toBe("$297,287")
  })
})

describe("numbers, percentages and ratios", () => {
  it("formats counts", () => {
    expect(formatNumber(1183)).toBe("1,183")
  })

  it("formats fractions as percentages", () => {
    expect(formatPercent(0.0918)).toBe("9.2%")
    expect(formatPercent(1.239142965, { decimals: 0 })).toBe("124%")
    expect(formatPercent(0.0406, { signed: true })).toBe("+4.1%")
  })

  it("formats rate differences as points", () => {
    expect(formatPoints(0.019)).toBe("+1.9 pts")
    expect(formatPoints(-0.013446)).toBe(`${MINUS}1.3 pts`)
  })

  it("formats ratios and months", () => {
    expect(formatRatio(2.4964)).toBe("2.5x")
    expect(formatMonths(6.436)).toBe("6.4 months")
    expect(formatMonths(1)).toBe("1.0 month")
  })
})

describe("KPI changes", () => {
  it("follows the API's change_type", () => {
    expect(formatChange(0.0406, "relative")).toBe("+4.1%")
    expect(formatChange(-0.0134, "absolute")).toBe(`${MINUS}1.3 pts`)
  })

  it("colors by direction and whether up is good", () => {
    expect(toneOf(0.04, true)).toBe("gain")
    expect(toneOf(-0.01, true)).toBe("loss")
    expect(toneOf(0.019, false)).toBe("loss") // churn going up is bad news
    expect(toneOf(-0.019, false)).toBe("gain")
    expect(toneOf(0, true)).toBe("neutral")
    expect(toneOf(null, true)).toBe("neutral")
  })
})

describe("months", () => {
  it("never shifts to the previous day, whatever the time zone", () => {
    expect(formatMonth("2026-08-01")).toBe("Aug 2026")
    expect(formatMonth("2026-08-01", "long")).toBe("August 2026")
    expect(formatMonth("2025-11-01", "month")).toBe("Nov")
  })

  it("names the last day of the month", () => {
    expect(formatMonthEnd("2026-08-01")).toBe("Aug 31, 2026")
    expect(formatMonthEnd("2024-02-01")).toBe("Feb 29, 2024")
  })
})

describe("formats for agent result columns", () => {
  it.each([
    ["logo_churn_rate", "percent"],
    ["gross_mrr_churn_rate", "percent"],
    ["nrr", "percent"],
    ["usage_trend", "percent"],
    ["churned_mrr", "currency"],
    ["expansion_mrr", "currency"],
    ["cac", "currency"],
    ["ltv_to_cac", "ratio"],
    ["payback_months", "months"],
    ["churned_customers", "number"],
    ["paying_customers", "number"],
  ])("%s -> %s", (column, format) => {
    expect(guessFormat(column)).toBe(format)
  })
})

describe("labels for agent result values", () => {
  it("names months, plans and channels", () => {
    expect(formatLabel("2026-08-01")).toBe("Aug 2026")
    expect(formatLabel("paid_ads")).toBe("Paid ads")
    expect(formatLabel("enterprise")).toBe("Enterprise")
    expect(formatLabel("Scott and Sons")).toBe("Scott and Sons")
  })
})
