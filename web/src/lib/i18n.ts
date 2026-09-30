// Every word the dashboard shows, in English and Spanish (Argentina). Findings
// are functions: they receive numbers already formatted for the language and
// put them in a sentence, because word order changes between languages.

import type { Channel } from "./types"
import type { Locale } from "./locale"

export interface Messages {
  htmlTitle: string
  header: {
    subtitle: string
    dataThrough: (date: string) => string
    language: string
  }
  theme: { toDark: string; toLight: string }
  period: { label: string; months: (count: number) => string }
  ask: {
    title: string
    intro: string
    questionLabel: string
    placeholder: string
    button: string
    thinking: string
    suggestionsLabel: string
    suggestions: string[]
    working: (question: string) => string
    showSql: string
    rowsShown: (shown: number, total: number) => string
    tryAgain: string
    unreachable: string
    notConfigured: string
    rateLimited: string
    failed: string
  }
  summary: {
    label: string
    lead: (month: string) => [before: string, after: string]
    leadChange: (
      direction: "up" | "down",
      change: string,
      previousMonth: string,
    ) => string
  }
  kpis: {
    mrr: string
    arr: string
    nrr: string
    logoChurn: string
    customers: string
    versus: (month: string) => string
  }
  mrrTrend: {
    finding: (direction: "grew" | "fell", from: string, to: string) => string
    fallback: string
    metric: (period: string) => string
    series: string
  }
  bridge: {
    finding: (winner: "expansion" | "churn", month: string) => string
    metric: (month: string, floor: string) => string
    steps: Record<BridgeStep, { label: string; short: string }>
  }
  byPlan: {
    finding: (plan: string, share: string) => string
    fallback: string
    metric: (period: string) => string
  }
  churn: {
    finding: (rate: string, month: string) => string
    fallback: string
    metric: (period: string) => string
    otherPlans: string
  }
  channels: {
    finding: (channel: string, ratio: string) => string
    fallback: string
    metric: string
    series: string
    names: Record<Channel, string>
  }
  atRisk: {
    finding: (total: number, high: number) => string
    metric: string
    customer: string
    plan: string
    mrr: string
    usage: string
    risk: string
    high: string
    medium: string
    empty: string
    emptyHint: string
  }
  states: {
    loading: string
    empty: string
    emptyHint: string
    error: string
    errorHint: string
    retry: string
    retrying: string
    dashboardError: string
  }
  periodRange: (from: string, to: string) => string
  footer: { synthetic: string; designSystem: string }
}

export type BridgeStep =
  | "lastMonth"
  | "new"
  | "expansion"
  | "contraction"
  | "churn"
  | "reactivation"
  | "thisMonth"

const en: Messages = {
  htmlTitle: "InsightFlow",
  header: {
    subtitle: "Revenue and retention of a B2B SaaS company",
    dataThrough: (date) => `data through ${date}`,
    language: "Language",
  },
  theme: { toDark: "Dark mode", toLight: "Light mode" },
  period: { label: "Period", months: (count) => `${count} months` },
  ask: {
    title: "Ask InsightFlow",
    intro:
      "Ask a question about revenue, churn or customers in plain language. An AI analyst answers from the same data as the charts below, and shows the query it ran.",
    questionLabel: "Your question",
    placeholder: "Type your question",
    button: "Ask",
    thinking: "Thinking…",
    suggestionsLabel: "Suggested questions",
    suggestions: [
      "What happened to Starter churn after the price change?",
      "Which acquisition channel has the highest churn rate?",
      "Why is net revenue retention above 100% if we are losing customers?",
      "Which paying customers are at high risk of churning?",
    ],
    working: (question) =>
      `Writing a query for “${question}”. This takes a few seconds.`,
    showSql: "Show the SQL behind this answer",
    rowsShown: (shown, total) => `Showing ${shown} of ${total} rows.`,
    tryAgain: "Try again in a moment.",
    unreachable: "The InsightFlow API could not be reached.",
    notConfigured: "The AI analyst is not configured on this server.",
    rateLimited: "Too many questions in a short time. Please wait a moment.",
    failed: "The analyst could not answer right now.",
  },
  summary: {
    label: "Summary",
    lead: (month) => ["MRR reached ", ` in ${month}`],
    leadChange: (direction, change, previousMonth) =>
      `, ${direction} ${change} on ${previousMonth}`,
  },
  kpis: {
    mrr: "MRR",
    arr: "ARR",
    nrr: "Net revenue retention",
    logoChurn: "Logo churn",
    customers: "Paying customers",
    versus: (month) => `vs ${month}`,
  },
  mrrTrend: {
    finding: (direction, from, to) => `MRR ${direction} from ${from} to ${to}`,
    fallback: "Monthly recurring revenue",
    metric: (period) => `Monthly recurring revenue at month end · ${period}`,
    series: "MRR",
  },
  bridge: {
    finding: (winner, month) =>
      winner === "expansion"
        ? `Expansion outweighed churn in ${month}`
        : `Churn outweighed expansion in ${month}`,
    metric: (month, floor) =>
      `How MRR moved in ${month} · axis starts at ${floor}`,
    steps: {
      lastMonth: { label: "Last month", short: "Start" },
      new: { label: "New", short: "New" },
      expansion: { label: "Expansion", short: "Exp." },
      contraction: { label: "Contraction", short: "Contr." },
      churn: { label: "Churn", short: "Churn" },
      reactivation: { label: "Reactivation", short: "React." },
      thisMonth: { label: "This month", short: "End" },
    },
  },
  byPlan: {
    finding: (plan, share) => `${plan} brings ${share} of MRR`,
    fallback: "MRR by plan",
    metric: (period) => `MRR by plan · ${period}`,
  },
  churn: {
    finding: (rate, month) => `Starter churn peaked at ${rate} in ${month}`,
    fallback: "Starter churn",
    metric: (period) => `Share of customers lost each month · ${period}`,
    otherPlans: "Other plans",
  },
  channels: {
    finding: (channel, ratio) =>
      `${channel} returns the least: a customer is worth ${ratio} what it cost`,
    fallback: "Return on acquisition by channel",
    metric:
      "Lifetime value of a customer divided by its acquisition cost · last 12 months",
    series: "LTV to CAC",
    names: {
      organic: "Organic",
      paid_ads: "Paid ads",
      partner: "Partner",
      outbound: "Outbound",
    },
  },
  atRisk: {
    finding: (total, high) =>
      `${total} paying customers are using the product less, ${high} of them sharply`,
    metric:
      "Sharpest declines first, then the largest accounts · usage is active users in the last 4 weeks against the 8 before",
    customer: "Customer",
    plan: "Plan",
    mrr: "MRR",
    usage: "Usage",
    risk: "Risk",
    high: "High",
    medium: "Medium",
    empty: "No customers at risk right now.",
    emptyHint: "Usage is steady everywhere.",
  },
  states: {
    loading: "Loading chart",
    empty: "No data for this period.",
    emptyHint: "Try a longer period.",
    error: "This chart could not be loaded.",
    errorHint:
      "The data service did not answer. It usually works on a second try.",
    retry: "Try again",
    retrying: "Trying again…",
    dashboardError: "The dashboard could not reach its data.",
  },
  periodRange: (from, to) => `${from} to ${to}`,
  footer: { synthetic: "Synthetic data.", designSystem: "Design system" },
}

const es: Messages = {
  htmlTitle: "InsightFlow",
  header: {
    subtitle: "Ingresos y retención de una empresa B2B SaaS",
    dataThrough: (date) => `datos al ${date}`,
    language: "Idioma",
  },
  theme: { toDark: "Modo oscuro", toLight: "Modo claro" },
  period: { label: "Período", months: (count) => `${count} meses` },
  ask: {
    title: "Preguntale a InsightFlow",
    intro:
      "Hacé una pregunta sobre ingresos, bajas o clientes en lenguaje natural. Un analista de IA responde con los mismos datos de los gráficos de abajo y muestra la consulta que usó.",
    questionLabel: "Tu pregunta",
    placeholder: "Escribí tu pregunta",
    button: "Preguntar",
    thinking: "Pensando…",
    suggestionsLabel: "Preguntas sugeridas",
    suggestions: [
      "¿Qué pasó con las bajas de Starter después de la suba de precio?",
      "¿Qué canal de adquisición tiene la tasa de bajas más alta?",
      "¿Por qué la retención neta de ingresos supera el 100% si perdemos clientes?",
      "¿Qué clientes pagos tienen alto riesgo de darse de baja?",
    ],
    working: (question) =>
      `Armando una consulta para “${question}”. Tarda unos segundos.`,
    showSql: "Ver la SQL de esta respuesta",
    rowsShown: (shown, total) => `Mostrando ${shown} de ${total} filas.`,
    tryAgain: "Probá de nuevo en un momento.",
    unreachable: "No se pudo conectar con la API de InsightFlow.",
    notConfigured: "El analista de IA no está configurado en este servidor.",
    rateLimited: "Demasiadas preguntas en poco tiempo. Esperá un momento.",
    failed: "El analista no pudo responder en este momento.",
  },
  summary: {
    label: "Resumen",
    lead: (month) => ["El MRR llegó a ", ` en ${month}`],
    leadChange: (direction, change, previousMonth) =>
      `, ${change} ${direction === "up" ? "más" : "menos"} que en ${previousMonth}`,
  },
  kpis: {
    mrr: "MRR",
    arr: "ARR",
    nrr: "Retención neta de ingresos",
    logoChurn: "Bajas de clientes",
    customers: "Clientes pagos",
    versus: (month) => `vs ${month}`,
  },
  mrrTrend: {
    finding: (direction, from, to) =>
      `El MRR ${direction === "grew" ? "creció" : "cayó"} de ${from} a ${to}`,
    fallback: "Ingresos recurrentes mensuales",
    metric: (period) =>
      `Ingresos recurrentes mensuales a fin de mes · ${period}`,
    series: "MRR",
  },
  bridge: {
    finding: (winner, month) =>
      winner === "expansion"
        ? `La expansión superó a las bajas en ${month}`
        : `Las bajas superaron a la expansión en ${month}`,
    metric: (month, floor) =>
      `Cómo se movió el MRR en ${month} · el eje arranca en ${floor}`,
    steps: {
      lastMonth: { label: "Mes anterior", short: "Inicio" },
      new: { label: "Nuevos", short: "Nuevos" },
      expansion: { label: "Expansión", short: "Exp." },
      contraction: { label: "Contracción", short: "Contr." },
      churn: { label: "Bajas", short: "Bajas" },
      reactivation: { label: "Reactivación", short: "React." },
      thisMonth: { label: "Este mes", short: "Fin" },
    },
  },
  byPlan: {
    finding: (plan, share) => `${plan} aporta el ${share} del MRR`,
    fallback: "MRR por plan",
    metric: (period) => `MRR por plan · ${period}`,
  },
  churn: {
    finding: (rate, month) =>
      `Las bajas de Starter tocaron un pico de ${rate} en ${month}`,
    fallback: "Bajas de Starter",
    metric: (period) => `Porcentaje de clientes perdidos cada mes · ${period}`,
    otherPlans: "Otros planes",
  },
  channels: {
    finding: (channel, ratio) =>
      `${channel} es el que menos rinde: un cliente vale ${ratio} lo que costó`,
    fallback: "Retorno de la adquisición por canal",
    metric:
      "Valor de vida de un cliente dividido por su costo de adquisición · últimos 12 meses",
    series: "LTV / CAC",
    names: {
      organic: "Orgánico",
      paid_ads: "Anuncios pagos",
      partner: "Partners",
      outbound: "Outbound",
    },
  },
  atRisk: {
    finding: (total, high) =>
      `${total} clientes pagos están usando menos el producto, ${high} de ellos de forma marcada`,
    metric:
      "Primero las caídas más fuertes, después las cuentas más grandes · uso: usuarios activos de las últimas 4 semanas contra las 8 anteriores",
    customer: "Cliente",
    plan: "Plan",
    mrr: "MRR",
    usage: "Uso",
    risk: "Riesgo",
    high: "Alto",
    medium: "Medio",
    empty: "No hay clientes en riesgo en este momento.",
    emptyHint: "El uso está estable en todas las cuentas.",
  },
  states: {
    loading: "Cargando gráfico",
    empty: "No hay datos para este período.",
    emptyHint: "Probá con un período más largo.",
    error: "No se pudo cargar este gráfico.",
    errorHint:
      "El servicio de datos no respondió. Suele funcionar al segundo intento.",
    retry: "Reintentar",
    retrying: "Reintentando…",
    dashboardError: "El tablero no pudo acceder a sus datos.",
  },
  periodRange: (from, to) => `${from} a ${to}`,
  footer: { synthetic: "Datos sintéticos.", designSystem: "Sistema de diseño" },
}

export const MESSAGES: Record<Locale, Messages> = { en, es }
