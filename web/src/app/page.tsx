import { Dashboard } from "@/components/dashboard/Dashboard"

// Rendered per request: the build may run without the API, and a build-time
// error state would be cached. API responses themselves stay cached.
export const dynamic = "force-dynamic"

export default function EnglishDashboard({
  searchParams,
}: {
  searchParams: Promise<{ period?: string | string[] }>
}) {
  return <Dashboard locale="en" searchParams={searchParams} />
}
