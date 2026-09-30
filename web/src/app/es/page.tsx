import type { Metadata } from "next"

import { Dashboard } from "@/components/dashboard/Dashboard"

export const metadata: Metadata = {
  description:
    "Analítica de una empresa B2B SaaS: ingresos, retención, clientes y un analista de IA.",
}

// Rendered per request, like the English page (see app/page.tsx).
export const dynamic = "force-dynamic"

export default function SpanishDashboard({
  searchParams,
}: {
  searchParams: Promise<{ period?: string | string[] }>
}) {
  return <Dashboard locale="es" searchParams={searchParams} />
}
