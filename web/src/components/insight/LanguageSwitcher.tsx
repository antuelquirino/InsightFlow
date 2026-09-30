import { MESSAGES } from "@/lib/i18n"
import { LOCALE_PATHS, LOCALES, type Locale } from "@/lib/locale"
import type { Period } from "@/lib/period"
import { Segmented } from "./PeriodFilter"

const SHORT_NAMES: Record<Locale, string> = { en: "EN", es: "ES" }

/** EN | ES. Each language has its own URL (/ and /es); the period carries over. */
export function LanguageSwitcher({
  current,
  period,
}: {
  current: Locale
  period: Period
}) {
  return (
    <Segmented
      label={MESSAGES[current].header.language}
      options={LOCALES.map((locale) => ({
        href: `${LOCALE_PATHS[locale]}?period=${period}`,
        text: SHORT_NAMES[locale],
        active: locale === current,
      }))}
    />
  )
}
