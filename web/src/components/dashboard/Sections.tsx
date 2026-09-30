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

const periodLabel = (range: Required<MonthRange>) =>
  `${formatMonth(`${range.start_month}-01`)} to ${formatMonth(`${range.end_month}-01`)}`

export async function MrrTrendSection({
  range,
}: {
  range: Required<MonthRange>
}) {
  const result = await loadOrNull(() => api.mrr(range))
  if (!result) return <ChartError />
  if (!result.series.length) return <ChartEmpty />
  return (
    <ChartSection
      finding={mrrTrendFinding(result.series)}
      metric={`Monthly recurring revenue at month end · ${periodLabel(range)}`}
    >
      <MetricLineChart
        data={result.series.map((point) => ({
          month: point.month,
          MRR: point.mrr,
        }))}
        categories={["MRR"]}
        colors={["ochre"]}
        valueFormat="currency"
      />
    </ChartSection>
  )
}

export async function BridgeSection({ month }: { month: string }) {
  const yyyyMm = month.slice(0, 7)
  const result = await loadOrNull(() =>
    api.mrrMovements({ start_month: yyyyMm, end_month: yyyyMm }),
  )
  if (!result) return <ChartError />
  const movements = result.months[0]
  if (!movements) return <ChartEmpty />
  const floor = bridgeAxisFloor(movements)
  return (
    <ChartSection
      finding={bridgeFinding(movements)}
      metric={`How MRR moved in ${formatMonth(month, "long")} · axis starts at ${formatCurrency(floor)}`}
    >
      <Waterfall steps={bridgeSteps(movements)} axisFloor={floor} />
    </ChartSection>
  )
}

export async function MrrByPlanSection({
  range,
}: {
  range: Required<MonthRange>
}) {
  const result = await loadOrNull(() =>
    api.mrr({ ...range, breakdown: "plan" }),
  )
  if (!result) return <ChartError />
  if (!result.series.length) return <ChartEmpty />
  const rows = mrrByPlanRows(result.series)
  return (
    <ChartSection
      finding={largestPlanFinding(rows)}
      metric={`MRR by plan · ${periodLabel(range)}`}
    >
      <MetricLineChart
        data={rows}
        categories={PLANS.map((plan) => PLAN_LABELS[plan])}
        colors={PLANS.map((plan) => PLAN_COLORS[plan])}
        valueFormat="currency"
      />
    </ChartSection>
  )
}

export async function ChurnByPlanSection({
  range,
}: {
  range: Required<MonthRange>
}) {
  const result = await loadOrNull(() =>
    api.churn({ ...range, breakdown: "plan" }),
  )
  if (!result) return <ChartError />
  if (!result.series.length) return <ChartEmpty />
  const rows = starterVsOthers(result.series)
  return (
    <ChartSection
      finding={starterPeakFinding(rows)}
      metric={`Share of customers lost each month · ${periodLabel(range)}`}
    >
      <MetricLineChart
        data={rows}
        categories={["Starter", "Other plans"]}
        colors={["ochre", "muted"]}
        valueFormat="percent"
      />
    </ChartSection>
  )
}

export async function ChannelsSection() {
  const result = await loadOrNull(() => api.unitEconomics())
  if (!result) return <ChartError />
  const { rows, weakest, finding } = channelReturns(result.channels)
  if (!rows.length) return <ChartEmpty />
  // Emphasis: the weakest channel in the accent, the others as context.
  const colors: AvailableChartColorsKeys[] = rows.map((row) =>
    weakest && row.channel === rows[rows.length - 1].channel
      ? "ochre"
      : "muted",
  )
  return (
    <ChartSection
      finding={finding}
      metric="Lifetime value of a customer divided by its acquisition cost · last 12 months"
    >
      <BarChart
        data={rows}
        index="channel"
        category="LTV to CAC"
        valueFormat="ratio"
        colors={colors}
      />
    </ChartSection>
  )
}

export async function AtRiskSection() {
  const result = await loadOrNull(() => api.atRisk({ limit: 200 }))
  if (!result) return <ChartError />
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
    <ChartSection
      finding={`${customers.length} paying customers are using the product less, ${high} of them sharply`}
      metric="Sharpest declines first, then the largest accounts · usage is active users in the last 4 weeks against the 8 before"
    >
      {shown.length ? (
        <div className="overflow-x-auto">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Customer</TableHeaderCell>
                <TableHeaderCell>Plan</TableHeaderCell>
                <TableHeaderCell className="text-right">MRR</TableHeaderCell>
                <TableHeaderCell className="text-right">Usage</TableHeaderCell>
                <TableHeaderCell>Risk</TableHeaderCell>
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
                    {formatCurrency(customer.current_mrr)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatPercent(customer.usage_trend - 1, {
                      decimals: 0,
                      signed: true,
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        customer.churn_risk === "high" ? "loss" : "neutral"
                      }
                    >
                      {customer.churn_risk === "high" ? "High" : "Medium"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <ChartEmpty
          message="No customers at risk right now."
          hint="Usage is steady everywhere."
        />
      )}
    </ChartSection>
  )
}
