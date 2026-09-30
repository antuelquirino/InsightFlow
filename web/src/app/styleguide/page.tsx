import type { Metadata } from "next"
import Link from "next/link"
import { Suspense } from "react"

import { Badge } from "@/components/Badge"
import { Button } from "@/components/Button"
import { Input } from "@/components/Input"
import { ChartSection, PageHeader } from "@/components/insight/ChartSection"
import { LeadFinding, Mark } from "@/components/insight/Finding"
import { KpiStrip } from "@/components/insight/KpiStrip"
import { MetricLineChart } from "@/components/insight/MetricChart"
import { PeriodFilter } from "@/components/insight/PeriodFilter"
import {
  ChartEmpty,
  ChartError,
  ChartLoading,
} from "@/components/insight/States"
import { api, loadOrNull } from "@/lib/api"
import { mrrLeadFinding } from "@/lib/findings"
import { formatCurrency, formatMonth, formatPercent } from "@/lib/format"
import { headlineKpis } from "@/lib/kpis"
import { periodRange } from "@/lib/period"
import { INTERFACE_COLORS, SERIES_COLORS, type ColorToken } from "@/lib/tokens"
import { cx, focusRing } from "@/lib/utils"

export const metadata: Metadata = { title: "Design system · InsightFlow" }

// Rendered per request, not at build time: the build may run where the API is
// unreachable, and a build-time error state would be cached. API responses are
// still cached (see lib/api.ts), so this costs little.
export const dynamic = "force-dynamic"

const PRINCIPLES = [
  [
    "One bold element",
    "Each screen opens with its finding as a sentence; the key figure wears an ochre marker. Everything else stays quiet.",
  ],
  [
    "Titles state the finding",
    "“Starter churn peaked in January”, not “Churn by plan”. The metric goes underneath, small.",
  ],
  [
    "Hairlines, not boxes",
    "No shadows, no gradients, no card around everything. Rules and white space do the separating.",
  ],
  [
    "The data is the only loud thing",
    "2px lines, thin bars, a barely-there grid, direct labels only where they matter.",
  ],
  [
    "Color has one job each",
    "Ochre is the accent. Gain and loss only mean improves and worsens, always with an arrow and a sign.",
  ],
  [
    "Motion answers the user",
    "Nothing animates on its own, and reduced-motion settings are respected.",
  ],
]

export default function StyleguidePage() {
  return (
    <div className="space-y-14 pb-16">
      <Link
        href="/"
        className={cx("text-sm text-graphite hover:text-ink", focusRing)}
      >
        ← Back to the dashboard
      </Link>
      <PageHeader
        title="Design system"
        note="The rules behind InsightFlow’s interface. Examples use live data from the API."
      />

      <section aria-labelledby="concept" className="space-y-6">
        <LeadFinding>
          An analyst’s report, <Mark>not a control panel</Mark>.
        </LeadFinding>
        <p className="max-w-2xl text-sm text-graphite">
          InsightFlow exists to tell findings, so it reads like a well-edited
          report: warm paper, ink instead of black, and every chart titled with
          what it shows. Light mode is the default; dark mode is a designed
          counterpart, not an inversion.
        </p>
        <h2 id="concept" className="sr-only">
          Principles
        </h2>
        <dl className="grid gap-x-10 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
          {PRINCIPLES.map(([title, text]) => (
            <div key={title} className="border-t border-rule pt-3">
              <dt className="text-sm font-medium text-ink">{title}</dt>
              <dd className="mt-1 text-sm text-graphite">{text}</dd>
            </div>
          ))}
        </dl>
      </section>

      <StyleSection
        title="Color"
        intro="Warm neutrals for almost everything, one accent, and two semantic colors used for nothing else. Each token has a light and a dark value."
      >
        <SwatchGrid tokens={INTERFACE_COLORS} />
      </StyleSection>

      <StyleSection
        title="Data colors"
        intro="Four series colors in a fixed order, validated together for colorblind separation (worst neighbor ΔE 12.5 light, 11.6 dark) and 3:1 contrast. An entity keeps its color on every screen; a fifth series becomes context gray, never a new hue."
      >
        <SwatchGrid tokens={SERIES_COLORS} />
      </StyleSection>

      <StyleSection
        title="Typography"
        intro="Newsreader, a serif made for reading news on screens, only for findings. IBM Plex Sans for the interface and every number, with tabular figures so numbers align."
      >
        <div className="divide-y divide-rule border-y border-rule">
          <TypeSpecimen spec="Newsreader 32 / 400 · lead finding">
            <p className="font-serif text-finding-lead text-ink">
              Expansion outweighed churn in <Mark>August</Mark>.
            </p>
          </TypeSpecimen>
          <TypeSpecimen spec="Newsreader 20 / 400 · chart finding">
            <p className="font-serif text-finding text-ink">
              Starter churn peaked after the price change
            </p>
          </TypeSpecimen>
          <TypeSpecimen spec="Plex Sans 20 / 600 · screen title">
            <p className="text-xl font-semibold text-ink">Retention</p>
          </TypeSpecimen>
          <TypeSpecimen spec="Plex Sans 28 / 600 · KPI value, tabular figures">
            <p className="text-kpi font-semibold text-ink tabular-nums">
              $297k · 124% · 4.3%
            </p>
          </TypeSpecimen>
          <TypeSpecimen spec="Plex Sans 14 / 400 · body">
            <p className="max-w-xl text-sm text-ink">
              Customers who pay for the first time in a month form that month’s
              cohort.
            </p>
          </TypeSpecimen>
          <TypeSpecimen spec="Plex Sans 12 / 400 · captions and axes">
            <p className="text-xs text-muted tabular-nums">
              Aug 2025 · Nov 2025 · Feb 2026 · May 2026
            </p>
          </TypeSpecimen>
        </div>
      </StyleSection>

      <StyleSection
        title="Findings and KPIs"
        intro="The lead finding is built from API data with a sentence template; the KPI strip is one ruled band. Change colors depend on whether up is good news: churn going up is a loss."
      >
        <Suspense fallback={<ChartLoading className="h-40" />}>
          <LiveLeadAndKpis />
        </Suspense>
      </StyleSection>

      <StyleSection
        title="Charts"
        intro="One series needs no legend. When the story is one series, it goes in ochre and the rest recede to context gray (emphasis). Months on the x axis, never days."
      >
        <div className="grid gap-x-10 gap-y-10 xl:grid-cols-2">
          <Suspense fallback={<ChartLoading />}>
            <LiveMrrChart />
          </Suspense>
          <Suspense fallback={<ChartLoading />}>
            <LiveStarterChurnChart />
          </Suspense>
        </div>
      </StyleSection>

      <StyleSection
        title="States"
        intro="Every chart has designed loading, empty and error states at the chart’s height. Loading is static; errors use ink and an icon, never the loss color."
      >
        <div className="grid gap-6 lg:grid-cols-3">
          <StateSpecimen label="Loading">
            <ChartLoading />
          </StateSpecimen>
          <StateSpecimen label="Empty">
            <ChartEmpty />
          </StateSpecimen>
          <StateSpecimen label="Error">
            <ChartError />
          </StateSpecimen>
        </div>
      </StyleSection>

      <StyleSection
        title="Controls"
        intro="One primary action per view, in the accent. The period filter is the only global filter; it lives in the URL."
      >
        <div className="flex flex-wrap items-center gap-3">
          <Button>Ask a question</Button>
          <Button variant="secondary">Show SQL</Button>
          <Button variant="ghost">Cancel</Button>
          <PeriodFilter current={12} basePath="/styleguide" />
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2">
          <Badge variant="gain">▲ +4.1%</Badge>
          <Badge variant="loss">▲ +1.9 pts churn</Badge>
          <Badge variant="neutral">No change</Badge>
          <Badge>High risk</Badge>
        </div>
        <div className="mt-5 max-w-sm">
          <Input
            type="search"
            placeholder="Search customers"
            aria-label="Search customers"
          />
        </div>
      </StyleSection>
    </div>
  )
}

// --- Live examples (server components; each fails on its own) -----------------

async function LiveLeadAndKpis() {
  const summary = await loadOrNull(() => api.summary())
  if (!summary) {
    return (
      <ChartError className="h-40" message="The KPIs could not be loaded." />
    )
  }
  const lead = mrrLeadFinding(summary)
  return (
    <div className="space-y-6">
      <LeadFinding>
        {lead.before}
        <Mark>{lead.mark}</Mark>
        {lead.after}
      </LeadFinding>
      <KpiStrip items={headlineKpis(summary)} />
    </div>
  )
}

async function LiveMrrChart() {
  const result = await loadOrNull(async () => {
    const summary = await api.summary()
    return api.mrr(periodRange(summary.month, 12))
  })
  if (!result) return <ChartError />
  const { series } = result
  if (!series.length) return <ChartEmpty />
  const first = series[0]
  const last = series[series.length - 1]
  return (
    <ChartSection
      finding={`MRR grew from ${formatCurrency(first.mrr)} to ${formatCurrency(last.mrr)} in a year`}
      metric={`MRR at month end · ${formatMonth(first.month)} to ${formatMonth(last.month)}`}
    >
      <MetricLineChart
        data={series.map((point) => ({ month: point.month, MRR: point.mrr }))}
        categories={["MRR"]}
        colors={["ochre"]}
        valueFormat="currency"
      />
    </ChartSection>
  )
}

async function LiveStarterChurnChart() {
  const result = await loadOrNull(async () => {
    const summary = await api.summary()
    return api.churn({ ...periodRange(summary.month, 12), breakdown: "plan" })
  })
  if (!result) return <ChartError />
  const { series } = result
  if (!series.length) return <ChartEmpty />
  // Starter against all other plans combined: emphasis, not three equal lines.
  const months = [...new Set(series.map((point) => point.month))]
  const data = months.map((month) => {
    const rows = series.filter((point) => point.month === month)
    const starter = rows.find((point) => point.group === "starter")
    const others = rows.filter((point) => point.group !== "starter")
    const atStart = others.reduce(
      (sum, point) => sum + point.customers_at_start,
      0,
    )
    const churned = others.reduce(
      (sum, point) => sum + point.churned_customers,
      0,
    )
    return {
      month,
      Starter: starter?.logo_churn_rate ?? null,
      "Other plans": atStart ? churned / atStart : null,
    }
  })
  const peak = data.reduce((best, row) =>
    (row.Starter ?? 0) > (best.Starter ?? 0) ? row : best,
  )
  return (
    <ChartSection
      finding={`Starter churn peaked at ${formatPercent(peak.Starter)} in ${formatMonth(peak.month, "long")}`}
      metric="Monthly logo churn, Starter against the other plans"
    >
      <MetricLineChart
        data={data}
        categories={["Starter", "Other plans"]}
        colors={["ochre", "muted"]}
        valueFormat="percent"
      />
    </ChartSection>
  )
}

// --- Page pieces ------------------------------------------------------------------

function StyleSection({
  title,
  intro,
  children,
}: {
  title: string
  intro: string
  children: React.ReactNode
}) {
  const id = title.toLowerCase().replace(/\s+/g, "-")
  return (
    <section aria-labelledby={id} className="border-t border-rule pt-8">
      <h2 id={id} className="text-lg font-semibold text-ink">
        {title}
      </h2>
      <p className="mt-1 max-w-2xl text-sm text-graphite">{intro}</p>
      <div className="mt-6">{children}</div>
    </section>
  )
}

function SwatchGrid({ tokens }: { tokens: ColorToken[] }) {
  return (
    <ul className="grid grid-cols-2 gap-x-6 gap-y-5 lg:grid-cols-3 xl:grid-cols-5">
      {tokens.map((token) => (
        <li key={token.variable}>
          {/* light and dark values side by side, whatever the current mode */}
          <div className="flex h-14 overflow-hidden rounded-md border border-rule">
            <div className="flex-1" style={{ backgroundColor: token.light }} />
            <div className="flex-1" style={{ backgroundColor: token.dark }} />
          </div>
          <p className="mt-2 text-sm font-medium text-ink">{token.name}</p>
          <p className="text-xs text-graphite">{token.role}</p>
          <p className="mt-0.5 font-mono text-xs text-muted">
            {token.light} · {token.dark}
          </p>
        </li>
      ))}
    </ul>
  )
}

function TypeSpecimen({
  spec,
  children,
}: {
  spec: string
  children: React.ReactNode
}) {
  return (
    <div className="grid gap-2 py-4 md:grid-cols-[14rem_1fr] md:items-baseline">
      <p className="text-xs text-muted">{spec}</p>
      {children}
    </div>
  )
}

function StateSpecimen({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <figure>
      {children}
      <figcaption className="mt-2 text-xs text-muted">{label}</figcaption>
    </figure>
  )
}
