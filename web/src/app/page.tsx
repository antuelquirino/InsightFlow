import Link from "next/link"
import { Suspense } from "react"

import {
  AtRiskSection,
  BridgeSection,
  ChannelsSection,
  ChurnByPlanSection,
  MrrByPlanSection,
  MrrTrendSection,
} from "@/components/dashboard/Sections"
import { AskPanel } from "@/components/insight/AskPanel"
import { LeadFinding, Mark } from "@/components/insight/Finding"
import { KpiStrip } from "@/components/insight/KpiStrip"
import { PeriodFilter } from "@/components/insight/PeriodFilter"
import { ChartError, ChartLoading } from "@/components/insight/States"
import { ThemeToggle } from "@/components/insight/ThemeToggle"
import { api, loadOrNull } from "@/lib/api"
import { mrrLeadFinding } from "@/lib/findings"
import { formatMonthEnd } from "@/lib/format"
import { headlineKpis } from "@/lib/kpis"
import { parsePeriod, periodRange } from "@/lib/period"
import { focusRing, cx } from "@/lib/utils"

// Rendered per request: the build may run without the API, and a build-time
// error state would be cached. API responses themselves stay cached.
export const dynamic = "force-dynamic"

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ period?: string | string[] }>
}) {
  const period = parsePeriod((await searchParams).period)
  const summary = await loadOrNull(() => api.summary())

  return (
    <div className="space-y-12 pb-16">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-rule pb-5">
        <div>
          <p className="font-serif text-2xl text-ink">InsightFlow</p>
          <p className="mt-0.5 text-sm text-muted">
            Revenue and retention of a B2B SaaS company
            {summary ? ` · data through ${formatMonthEnd(summary.month)}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <PeriodFilter current={period} basePath="/" />
          <ThemeToggle />
        </div>
      </header>

      {/* The AI analyst leads the page: the one boxed element, so it reads as
          the place to start. It works even if the charts cannot load. */}
      <section
        aria-labelledby="ask-title"
        className="rounded-lg border border-rule bg-surface p-5 sm:p-7"
      >
        <h2
          id="ask-title"
          className="font-serif text-[1.625rem] leading-tight text-ink"
        >
          Ask InsightFlow
        </h2>
        <p className="mt-1 mb-5 max-w-2xl text-sm text-graphite">
          Ask a question about revenue, churn or customers in plain language. An
          AI analyst answers from the same data as the charts below, and shows
          the query it ran.
        </p>
        <AskPanel />
      </section>

      {!summary ? (
        <ChartError message="The dashboard could not reach its data." />
      ) : (
        <>
          <section aria-label="Summary" className="space-y-6">
            <LeadFindingFor summary={summary} />
            <KpiStrip items={headlineKpis(summary)} />
          </section>

          <div className="grid grid-cols-1 gap-x-12 gap-y-12 xl:grid-cols-2">
            <Suspense fallback={<ChartLoading />}>
              <MrrTrendSection range={periodRange(summary.month, period)} />
            </Suspense>
            <Suspense fallback={<ChartLoading />}>
              <BridgeSection month={summary.month} />
            </Suspense>
            <Suspense fallback={<ChartLoading />}>
              <MrrByPlanSection range={periodRange(summary.month, period)} />
            </Suspense>
            <Suspense fallback={<ChartLoading />}>
              <ChurnByPlanSection range={periodRange(summary.month, period)} />
            </Suspense>
            <Suspense fallback={<ChartLoading />}>
              <ChannelsSection />
            </Suspense>
            <Suspense fallback={<ChartLoading />}>
              <AtRiskSection />
            </Suspense>
          </div>
        </>
      )}

      <footer className="border-t border-rule pt-5 text-xs text-muted">
        Synthetic data.{" "}
        <Link
          href="/styleguide"
          className={cx(
            "underline decoration-rule underline-offset-2 hover:text-ink",
            focusRing,
          )}
        >
          Design system
        </Link>
      </footer>
    </div>
  )
}

function LeadFindingFor({
  summary,
}: {
  summary: Awaited<ReturnType<typeof api.summary>>
}) {
  const lead = mrrLeadFinding(summary)
  return (
    <LeadFinding>
      {lead.before}
      <Mark>{lead.mark}</Mark>
      {lead.after}
    </LeadFinding>
  )
}
