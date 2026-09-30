// Server-side client for the InsightFlow API. Metric screens fetch here, in
// server components, so the browser never needs the API for dashboard data.

import type {
  AtRiskResponse,
  Channel,
  ChurnResponse,
  MrrMovementsResponse,
  MrrResponse,
  Plan,
  RetentionResponse,
  SummaryResponse,
  UnitEconomicsResponse,
} from "./types"

const API_URL = process.env.API_URL ?? "http://localhost:8000"

// The data is static; the API caches it too. An hour keeps pages fast without
// ever serving something stale for long after a reload of the data.
const REVALIDATE_SECONDS = 3600

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

type Params = Record<string, string | number | string[] | undefined>

async function get<T>(path: string, params: Params = {}): Promise<T> {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue
    for (const item of Array.isArray(value) ? value : [value]) {
      url.searchParams.append(key, String(item))
    }
  }
  let response: Response
  try {
    response = await fetch(url, { next: { revalidate: REVALIDATE_SECONDS } })
  } catch {
    throw new ApiError("The InsightFlow API could not be reached.")
  }
  if (!response.ok) {
    throw new ApiError(
      `The API answered ${response.status} for ${path}.`,
      response.status,
    )
  }
  return (await response.json()) as T
}

export interface MonthRange {
  start_month?: string // YYYY-MM
  end_month?: string
}

export const api = {
  summary: (month?: string) =>
    get<SummaryResponse>("/metrics/summary", { month }),
  mrr: (
    options: MonthRange & {
      breakdown?: "total" | "plan" | "channel" | "company_size"
      plan?: Plan
      channel?: Channel
    } = {},
  ) => get<MrrResponse>("/metrics/mrr", { ...options }),
  mrrMovements: (range: MonthRange = {}) =>
    get<MrrMovementsResponse>("/metrics/mrr-movements", { ...range }),
  churn: (
    options: MonthRange & { breakdown?: "total" | "plan" | "channel" } = {},
  ) => get<ChurnResponse>("/metrics/churn", { ...options }),
  retention: (options: MonthRange & { max_months?: number } = {}) =>
    get<RetentionResponse>("/metrics/retention", { ...options }),
  unitEconomics: (month?: string) =>
    get<UnitEconomicsResponse>("/metrics/unit-economics", { month }),
  atRisk: (options: { risk?: ("high" | "medium")[]; limit?: number } = {}) =>
    get<AtRiskResponse>("/customers/at-risk", { ...options }),
}

/**
 * Runs API calls and returns null if any of them fails, so a server component
 * can render its error state without wrapping JSX in try/catch (which would
 * also swallow rendering bugs).
 */
export async function loadOrNull<T>(load: () => Promise<T>): Promise<T | null> {
  try {
    return await load()
  } catch (error) {
    if (error instanceof ApiError) return null
    throw error
  }
}
