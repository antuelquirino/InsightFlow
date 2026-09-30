"use client"

// The AI analyst, on the dashboard itself. The browser calls POST /ask on the
// API directly (CORS allows this site); the API validates the SQL, runs it and
// writes the answer from the real rows, in the language of the question.

import { RiArrowRightLine, RiSparkling2Line } from "@remixicon/react"
import { useState } from "react"

import { Button } from "@/components/Button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from "@/components/Table"
import type { ChartDatum } from "@/lib/chartUtils"
import { MESSAGES, type Messages } from "@/lib/i18n"
import type { Locale } from "@/lib/locale"
import type { AskResponse } from "@/lib/types"
import { cx, focusInput, focusRing } from "@/lib/utils"
import { BarChart } from "./BarChart"
import { MetricLineChart } from "./MetricChart"
import {
  formatLabel,
  formatterFor,
  guessFormat,
  isIsoDate,
} from "./valueFormats"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type State =
  | { kind: "idle" }
  | { kind: "loading"; question: string }
  | { kind: "done"; question: string; result: AskResponse }
  | { kind: "error"; question: string; message: string }

export function AskPanel({ locale = "en" }: { locale?: Locale }) {
  const t = MESSAGES[locale].ask
  const [question, setQuestion] = useState("")
  const [state, setState] = useState<State>({ kind: "idle" })

  async function ask(text: string) {
    const trimmed = text.trim()
    if (trimmed.length < 3 || state.kind === "loading") return
    setQuestion(trimmed)
    setState({ kind: "loading", question: trimmed })
    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      })
      if (!response.ok) {
        throw new Error(
          response.status === 429
            ? t.rateLimited
            : response.status === 503
              ? t.notConfigured
              : t.failed,
        )
      }
      setState({
        kind: "done",
        question: trimmed,
        result: await response.json(),
      })
    } catch (error) {
      setState({
        kind: "error",
        question: trimmed,
        message:
          error instanceof TypeError ? t.unreachable : (error as Error).message,
      })
    }
  }

  return (
    <div className="space-y-5">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          ask(question)
        }}
        className="flex flex-col gap-2 sm:flex-row"
      >
        <label htmlFor="ask-question" className="sr-only">
          {t.questionLabel}
        </label>
        <input
          id="ask-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={t.placeholder}
          maxLength={500}
          className={cx(
            "w-full rounded-md border border-rule bg-paper px-3.5 py-2.5 text-base text-ink placeholder:text-muted",
            focusInput,
          )}
        />
        <Button
          type="submit"
          className="px-5 text-base"
          disabled={state.kind === "loading" || question.trim().length < 3}
        >
          {state.kind === "loading" ? t.thinking : t.button}
        </Button>
      </form>

      <div className="flex flex-wrap gap-2" aria-label={t.suggestionsLabel}>
        {t.suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => ask(suggestion)}
            disabled={state.kind === "loading"}
            className={cx(
              "inline-flex items-center gap-1.5 rounded-full border border-rule bg-paper px-3 py-1 text-left text-xs text-graphite transition-colors hover:border-ochre hover:text-ink disabled:opacity-50",
              focusRing,
            )}
          >
            <RiArrowRightLine
              className="size-3.5 shrink-0"
              aria-hidden="true"
            />
            {suggestion}
          </button>
        ))}
      </div>

      <div aria-live="polite" className="empty:hidden">
        {state.kind === "loading" ? (
          <p className="border-t border-rule pt-5 text-sm text-graphite">
            {t.working(state.question)}
          </p>
        ) : null}
        {state.kind === "error" ? (
          <div role="alert" className="border-t border-rule pt-5">
            <p className="text-sm font-medium text-ink">{state.message}</p>
            <p className="mt-1 text-sm text-muted">{t.tryAgain}</p>
          </div>
        ) : null}
        {state.kind === "done" ? (
          <Answer result={state.result} locale={locale} t={t} />
        ) : null}
      </div>
    </div>
  )
}

type AskMessages = Messages["ask"]

function Answer({
  result,
  locale,
  t,
}: {
  result: AskResponse
  locale: Locale
  t: AskMessages
}) {
  return (
    <article className="space-y-5 border-t border-rule pt-5">
      <div className="flex gap-3">
        <RiSparkling2Line
          className="mt-1 size-5 shrink-0 text-ochre"
          aria-hidden="true"
        />
        <div>
          <p className="font-serif text-finding text-ink">{result.answer}</p>
          {result.insight ? (
            <p className="mt-2 text-sm text-graphite">{result.insight}</p>
          ) : null}
        </div>
      </div>
      {result.status === "answered" && result.rows.length ? (
        <>
          <AnswerChart result={result} locale={locale} />
          <ResultTable result={result} locale={locale} t={t} />
        </>
      ) : null}
      {result.sql ? (
        <details className="group text-sm">
          <summary
            className={cx(
              "cursor-pointer rounded-sm text-graphite hover:text-ink",
              focusRing,
            )}
          >
            {t.showSql}
          </summary>
          <pre className="mt-2 overflow-x-auto rounded-md border border-rule bg-paper p-3 font-mono text-xs whitespace-pre-wrap text-graphite">
            {result.sql}
          </pre>
        </details>
      ) : null}
    </article>
  )
}

// The chart the API suggests, drawn with the dashboard's own components.
function AnswerChart({
  result,
  locale,
}: {
  result: AskResponse
  locale: Locale
}) {
  const { chart, rows } = result
  const y = chart.y[0]
  if (!y) return null
  const format = guessFormat(y)
  if (chart.type === "number") {
    const value = rows[0]?.[y]
    return typeof value === "number" ? (
      <p className="text-kpi font-semibold text-ink tabular-nums">
        {formatterFor(format, locale)(value)}
      </p>
    ) : null
  }
  const x = chart.x
  if (!x) return null
  const data = rows as ChartDatum[]
  if (chart.type === "line" && rows.every((row) => isIsoDate(row[x]))) {
    return (
      <MetricLineChart
        data={data}
        index={x}
        categories={chart.y}
        colors={chart.y.length > 1 ? ["ochre", "teal"] : ["ochre"]}
        valueFormat={format}
        locale={locale}
      />
    )
  }
  if (chart.type === "bar" || chart.type === "line") {
    return (
      <BarChart
        data={data}
        index={x}
        category={y}
        valueFormat={format}
        locale={locale}
      />
    )
  }
  return null
}

function ResultTable({
  result,
  locale,
  t,
}: {
  result: AskResponse
  locale: Locale
  t: AskMessages
}) {
  const shown = result.rows.slice(0, 12)
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHead>
          <TableRow>
            {result.columns.map((column) => (
              <TableHeaderCell
                key={column}
                className="text-xs whitespace-nowrap"
              >
                {column.replaceAll("_", " ")}
              </TableHeaderCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {shown.map((row, index) => (
            <TableRow key={index}>
              {result.columns.map((column) => {
                const value = row[column]
                return (
                  <TableCell
                    key={column}
                    className={cx(
                      "py-1.5 text-sm whitespace-nowrap",
                      typeof value === "number" && "text-right tabular-nums",
                    )}
                  >
                    {typeof value === "number"
                      ? formatterFor(guessFormat(column), locale)(value)
                      : formatLabel(value, locale)}
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {result.rows.length > shown.length ? (
        <p className="mt-2 text-xs text-muted">
          {t.rowsShown(shown.length, result.rows.length)}
        </p>
      ) : null}
    </div>
  )
}
