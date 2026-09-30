// The languages the dashboard speaks. English is the default and lives at "/";
// Spanish, with Argentine number and date formats, lives at "/es".

export type Locale = "en" | "es"

export const LOCALES: Locale[] = ["en", "es"]
export const DEFAULT_LOCALE: Locale = "en"

export const LOCALE_PATHS: Record<Locale, string> = { en: "/", es: "/es" }

/** The Intl locale behind each language's numbers and dates. */
export const INTL_LOCALES: Record<Locale, string> = { en: "en-US", es: "es-AR" }
