import Link from "next/link"

import { PERIODS, type Period } from "@/lib/period"
import { cx, focusRing } from "@/lib/utils"

/**
 * The one global filter: last 6, 12 or 24 months. Plain links that set
 * ?period=, so the choice survives reloads and can be shared as a URL.
 */
export function PeriodFilter({
  current,
  basePath,
}: {
  current: Period
  basePath: string
}) {
  return (
    <nav aria-label="Period">
      <ul className="flex rounded-md border border-rule bg-surface p-0.5 text-sm">
        {PERIODS.map((period) => {
          const active = period === current
          return (
            <li key={period}>
              <Link
                href={`${basePath}?period=${period}`}
                aria-current={active ? "true" : undefined}
                scroll={false}
                className={cx(
                  "block rounded-[5px] px-3 py-1 tabular-nums transition-colors",
                  active
                    ? "bg-ink font-medium text-paper"
                    : "text-graphite hover:bg-wash hover:text-ink",
                  focusRing,
                )}
              >
                {period} months
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
