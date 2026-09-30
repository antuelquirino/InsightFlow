"use client"
import { siteConfig } from "@/app/siteConfig"
import { ThemeToggle } from "@/components/insight/ThemeToggle"
import { cx, focusRing } from "@/lib/utils"
import Link from "next/link"
import { usePathname } from "next/navigation"
import MobileSidebar from "./MobileSidebar"
import { isActive, navigation } from "./navigation"

export function Wordmark({ className }: { className?: string }) {
  return (
    <Link
      href={siteConfig.baseLinks.home}
      className={cx(
        "rounded-sm font-serif text-xl text-ink",
        focusRing,
        className,
      )}
    >
      {siteConfig.name}
    </Link>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const styleguideActive = isActive(pathname, siteConfig.baseLinks.styleguide)
  return (
    <>
      {/* sidebar (lg+) */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-60 lg:flex-col">
        <aside className="flex grow flex-col gap-y-8 overflow-y-auto border-r border-rule bg-paper px-5 py-6">
          <Wordmark className="px-2" />
          <nav aria-label="Sections" className="flex flex-1 flex-col">
            <ul role="list" className="space-y-0.5">
              {navigation.map((item) => {
                const active = isActive(pathname, item.href)
                return (
                  <li key={item.name}>
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      className={cx(
                        // the active section: an ochre bar and ink text, no filled pill
                        "relative flex items-center gap-x-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                        active
                          ? "font-medium text-ink before:absolute before:inset-y-1.5 before:-left-3 before:w-0.5 before:rounded-full before:bg-ochre"
                          : "text-graphite hover:bg-wash hover:text-ink",
                        focusRing,
                      )}
                    >
                      <item.icon
                        className="size-4 shrink-0"
                        aria-hidden="true"
                      />
                      {item.name}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>
          <div className="space-y-1 border-t border-rule pt-4">
            <ThemeToggle />
            <Link
              href={siteConfig.baseLinks.styleguide}
              aria-current={styleguideActive ? "page" : undefined}
              className={cx(
                "block rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-wash hover:text-ink",
                styleguideActive ? "font-medium text-ink" : "text-muted",
                focusRing,
              )}
            >
              Design system
            </Link>
          </div>
        </aside>
      </div>
      {/* top bar (xs-lg) */}
      <div className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b border-rule bg-paper px-4 lg:hidden">
        <Wordmark />
        <MobileSidebar />
      </div>
    </>
  )
}
