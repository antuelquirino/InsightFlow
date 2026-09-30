// The dashboard's sections. Each is a server component that fetches its own
// data and fails on its own: one chart erroring never takes the page down.

import { Badge } from "@/components/Badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/Table"
import { BarChart } from "@/components/insight/BarChart"
import { ChartSection } from "@/components/insight/ChartSection"
import { MetricLineChart } from "@/components/insight/MetricChart"
import { ChartEmpty, ChartError } from "@/components/insight/States"
import { Waterfall } from "@/components/insight/Waterfall"
import { api, loadOrNull, type MonthRange } from "@/lib/api"
import type { AvailableChartColorsKeys } from "@/lib/chartUtils"
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
} from "@/lib/dashboardData"
import { PLAN_COLORS, PLAN_LABELS, PLANS } from "@/lib/entities"
import { formatCurrency, formatMonth, formatPercent } from "@/lib/format"
import { MESSAGES } from "@/lib/i18n"
import type { Locale } from "@/lib/locale"

type Range = Required<MonthRange>

interface SectionProps {
  locale: Locale
}

const periodLabel = (range: Range, locale: Locale) =>
  MESSAGES[locale].periodRange(
    formatMonth(`${range.start_month}-01`, "short", { locale }),
    formatMonth(`${range.end_month}-01`, "short", { locale }),
  )

export async function MrrTrendSection({
  range,
  locale,
}: SectionProps & { range: Range }) {
  const t = MESSAGES[locale].mrrTrend
  const result = await loadOrNull(() => api.mrr(range))
  if (!result) return <ChartError locale={locale} />
  if (!result.series.length) return <ChartEmpty locale={locale} />
  return (
    <ChartSection
      finding={mrrTrendFinding(result.series, locale)}
      metric={t.metric(periodLabel(range, locale))}
    >
      <MetricLineChart
        data={result.series.map((point) => ({
          month: point.month,
          [t.series]: point.mrr,
        }))}
        categories={[t.series]}
        colors={["ochre"]}
        valueFormat="currency"
        locale={locale}
      />
    </ChartSection>
  )
}

export async function BridgeSection({
  month,
  locale,
}: SectionProps & { month: string }) {
  const yyyyMm = month.slice(0, 7)
  const result = await loadOrNull(() =>
    api.mrrMovements({ start_month: yyyyMm, end_month: yyyyMm }),
  )
  if (!result) return <ChartError locale={locale} />
  const movements = result.months[0]
  if (!movements) return <ChartEmpty locale={locale} />
  const floor = bridgeAxisFloor(movements)
  return (
    <ChartSection
      finding={bridgeFinding(movements, locale)}
      metric={MESSAGES[locale].bridge.metric(
        formatMonth(month, "long", { locale }),
        formatCurrency(floor, { locale }),
      )}
    >
      <Waterfall
        steps={bridgeSteps(movements, locale)}
        axisFloor={floor}
        locale={locale}
      />
    </ChartSection>
  )
}

export async function MrrByPlanSection({
  range,
  locale,
}: SectionProps & { range: Range }) {
  const result = await loadOrNull(() =>
    api.mrr({ ...range, breakdown: "plan" }),
  )
  if (!result) return <ChartError locale={locale} />
  if (!result.series.length) return <ChartEmpty locale={locale} />
  const rows = mrrByPlanRows(result.series)
  return (
    <ChartSection
      finding={largestPlanFinding(rows, locale)}
      metric={MESSAGES[locale].byPlan.metric(periodLabel(range, locale))}
    >
      <MetricLineChart
        data={rows}
        categories={PLANS.map((plan) => PLAN_LABELS[plan])}
        colors={PLANS.map((plan) => PLAN_COLORS[plan])}
        valueFormat="currency"
        locale={locale}
      />
    </ChartSection>
  )
}

export async function ChurnByPlanSection({
  range,
  locale,
}: SectionProps & { range: Range }) {
  const t = MESSAGES[locale].churn
  const result = await loadOrNull(() =>
    api.churn({ ...range, breakdown: "plan" }),
  )
  if (!result) return <ChartError locale={locale} />
  if (!result.series.length) return <ChartEmpty locale={locale} />
  const rows = starterVsOthers(result.series, locale)
  return (
    <ChartSection
      finding={starterPeakFinding(rows, locale)}
      metric={t.metric(periodLabel(range, locale))}
    >
      <MetricLineChart
        data={rows}
        categories={["Starter", t.otherPlans]}
        colors={["ochre", "muted"]}
        valueFormat="percent"
        locale={locale}
      />
    </ChartSection>
  )
}

export async function ChannelsSection({ locale }: SectionProps) {
  const result = await loadOrNull(() => api.unitEconomics())
  if (!result) return <ChartError locale={locale} />
  const { rows, series, weakest, finding } = channelReturns(
    result.channels,
    locale,
  )
  if (!rows.length) return <ChartEmpty locale={locale} />
  // Emphasis: the weakest channel in the accent, the others as context.
  const colors: AvailableChartColorsKeys[] = rows.map((_, index) =>
    weakest && index === rows.length - 1 ? "ochre" : "muted",
  )
  return (
    <ChartSection finding={finding} metric={MESSAGES[locale].channels.metric}>
      <BarChart
        data={rows}
        index="channel"
        category={series}
        valueFormat="ratio"
        colors={colors}
        locale={locale}
      />
    </ChartSection>
  )
}

export async function AtRiskSection({ locale }: SectionProps) {
  const t = MESSAGES[locale].atRisk
  const result = await loadOrNull(() => api.atRisk({ limit: 200 }))
  if (!result) return <ChartError locale={locale} />
  const customers = result.customers
  const high = customers.filter(
    (customer) => customer.churn_risk === "high",
  ).length
  // The API sorts by MRR; show the sharpest declines first, largest first within each.
  const shown = [...customers]
    .sort(
      (a, b) =>
        Number(b.churn_risk === "high") - Number(a.churn_risk === "high"),
    )
    .slice(0, 8)
  return (
    <ChartSection finding={t.finding(customers.length, high)} metric={t.metric}>
      {shown.length ? (
        <div className="overflow-x-auto">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>{t.customer}</TableHeaderCell>
                <TableHeaderCell>{t.plan}</TableHeaderCell>
                <TableHeaderCell className="text-right">
                  {t.mrr}
                </TableHeaderCell>
                <TableHeaderCell className="text-right">
                  {t.usage}
                </TableHeaderCell>
                <TableHeaderCell>{t.risk}</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {shown.map((customer) => (
                <TableRow key={customer.organization_id}>
                  <TableCell className="font-medium whitespace-nowrap text-ink">
                    {customer.organization_name}
                  </TableCell>
                  <TableCell>{PLAN_LABELS[customer.current_plan_id]}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatCurrency(customer.current_mrr, { locale })}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatPercent(customer.usage_trend - 1, {
                      decimals: 0,
                      signed: true,
                      locale,
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        customer.churn_risk === "high" ? "loss" : "neutral"
                      }
                    >
                      {customer.churn_risk === "high" ? t.high : t.medium}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <ChartEmpty locale={locale} message={t.empty} hint={t.emptyHint} />
      )}
    </ChartSection>
  )
}
