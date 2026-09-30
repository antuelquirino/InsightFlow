import Link from "next/link"

import { MESSAGES } from "@/lib/i18n"
import type { Locale } from "@/lib/locale"
import { PERIODS, type Period } from "@/lib/period"
import { cx, focusRing } from "@/lib/utils"

/** A row of linked options with the current one filled in ink. */
export function Segmented({
  label,
  options,
}: {
  label: string
  options: { href: string; text: string; active: boolean }[]
}) {
  return (
    <nav aria-label={label}>
      <ul className="flex rounded-md border border-rule bg-surface p-0.5 text-sm">
        {options.map((option) => (
          <li key={option.href}>
            <Link
              href={option.href}
              aria-current={option.active ? "true" : undefined}
              scroll={false}
              className={cx(
                "block rounded-[5px] px-3 py-1 tabular-nums transition-colors",
                option.active
                  ? "bg-ink font-medium text-paper"
                  : "text-graphite hover:bg-wash hover:text-ink",
                focusRing,
              )}
            >
              {option.text}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}

/**
 * The one global filter: last 6, 12 or 24 months. Plain links that set
 * ?period=, so the choice survives reloads and can be shared as a URL.
 */
export function PeriodFilter({
  current,
  basePath,
  locale = "en",
}: {
  current: Period
  basePath: string
  locale?: Locale
}) {
  const t = MESSAGES[locale].period
  return (
    <Segmented
      label={t.label}
      options={PERIODS.map((period) => ({
        href: `${basePath}?period=${period}`,
        text: t.months(period),
        active: period === current,
      }))}
    />
  )
}
