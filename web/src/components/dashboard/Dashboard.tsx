import Link from "next/link"
import { Suspense } from "react"

import { AskPanel } from "@/components/insight/AskPanel"
import { LeadFinding, Mark } from "@/components/insight/Finding"
import { KpiStrip } from "@/components/insight/KpiStrip"
import { LanguageSwitcher } from "@/components/insight/LanguageSwitcher"
import { PeriodFilter } from "@/components/insight/PeriodFilter"
import { ChartError, ChartLoading } from "@/components/insight/States"
import { ThemeToggle } from "@/components/insight/ThemeToggle"
import { api, loadOrNull } from "@/lib/api"
import { mrrLeadFinding } from "@/lib/findings"
import { formatMonthEnd } from "@/lib/format"
import { MESSAGES } from "@/lib/i18n"
import { headlineKpis } from "@/lib/kpis"
import { LOCALE_PATHS, type Locale } from "@/lib/locale"
import { parsePeriod, periodRange } from "@/lib/period"
import type { SummaryResponse } from "@/lib/types"
import { cx, focusRing } from "@/lib/utils"
import {
  AtRiskSection,
  BridgeSection,
  ChannelsSection,
  ChurnByPlanSection,
  MrrByPlanSection,
  MrrTrendSection,
} from "./Sections"

/** The whole dashboard in one page, in one language. */
export async function Dashboard({
  locale,
  searchParams,
}: {
  locale: Locale
  searchParams: Promise<{ period?: string | string[] }>
}) {
  const t = MESSAGES[locale]
  const period = parsePeriod((await searchParams).period)
  const summary = await loadOrNull(() => api.summary())

  return (
    <div className="space-y-12 pb-16">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-rule pb-5">
        <div>
          <p className="font-serif text-2xl text-ink">InsightFlow</p>
          <p className="mt-0.5 text-sm text-muted">
            {t.header.subtitle}
            {summary
              ? ` · ${t.header.dataThrough(formatMonthEnd(summary.month, { locale }))}`
              : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <PeriodFilter
            current={period}
            basePath={LOCALE_PATHS[locale]}
            locale={locale}
          />
          <LanguageSwitcher current={locale} period={period} />
          <ThemeToggle locale={locale} />
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
          {t.ask.title}
        </h2>
        <p className="mt-1 mb-5 max-w-2xl text-sm text-graphite">
          {t.ask.intro}
        </p>
        <AskPanel locale={locale} />
      </section>

      {!summary ? (
        <ChartError locale={locale} message={t.states.dashboardError} />
      ) : (
        <>
          <section aria-label={t.summary.label} className="space-y-6">
            <Lead summary={summary} locale={locale} />
            <KpiStrip items={headlineKpis(summary, locale)} />
          </section>

          <div className="grid grid-cols-1 gap-x-12 gap-y-12 xl:grid-cols-2">
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <MrrTrendSection
                range={periodRange(summary.month, period)}
                locale={locale}
              />
            </Suspense>
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <BridgeSection month={summary.month} locale={locale} />
            </Suspense>
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <MrrByPlanSection
                range={periodRange(summary.month, period)}
                locale={locale}
              />
            </Suspense>
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <ChurnByPlanSection
                range={periodRange(summary.month, period)}
                locale={locale}
              />
            </Suspense>
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <ChannelsSection locale={locale} />
            </Suspense>
            <Suspense fallback={<ChartLoading locale={locale} />}>
              <AtRiskSection locale={locale} />
            </Suspense>
          </div>
        </>
      )}

      <footer className="border-t border-rule pt-5 text-xs text-muted">
        {t.footer.synthetic}{" "}
        <Link
          href="/styleguide"
          className={cx(
            "underline decoration-rule underline-offset-2 hover:text-ink",
            focusRing,
          )}
        >
          {t.footer.designSystem}
        </Link>
      </footer>
    </div>
  )
}

function Lead({
  summary,
  locale,
}: {
  summary: SummaryResponse
  locale: Locale
}) {
  const lead = mrrLeadFinding(summary, locale)
  return (
    <LeadFinding>
      {lead.before}
      <Mark>{lead.mark}</Mark>
      {lead.after}
    </LeadFinding>
  )
}
