import { siteConfig } from "@/app/siteConfig"
import { Button } from "@/components/Button"
import {
  Drawer,
  DrawerBody,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/Drawer"
import { ThemeToggle } from "@/components/insight/ThemeToggle"
import { cx, focusRing } from "@/lib/utils"
import { RiMenuLine } from "@remixicon/react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { isActive, navigation } from "./navigation"

export default function MobileSidebar() {
  const pathname = usePathname()
  return (
    <Drawer>
      <DrawerTrigger asChild>
        <Button
          variant="ghost"
          aria-label="Open navigation"
          className="group flex items-center rounded-md p-2 text-sm font-medium hover:bg-wash data-[state=open]:bg-wash"
        >
          <RiMenuLine
            className="size-6 shrink-0 sm:size-5"
            aria-hidden="true"
          />
        </Button>
      </DrawerTrigger>
      <DrawerContent className="sm:max-w-lg">
        <DrawerHeader>
          <DrawerTitle className="font-serif text-xl font-normal">
            {siteConfig.name}
          </DrawerTitle>
        </DrawerHeader>
        <DrawerBody>
          <nav aria-label="Sections" className="flex flex-1 flex-col">
            <ul role="list" className="space-y-1.5">
              {navigation.map((item) => (
                <li key={item.name}>
                  <DrawerClose asChild>
                    <Link
                      href={item.href}
                      aria-current={
                        isActive(pathname, item.href) ? "page" : undefined
                      }
                      className={cx(
                        isActive(pathname, item.href)
                          ? "bg-wash font-medium text-ink"
                          : "text-graphite hover:text-ink",
                        "flex items-center gap-x-2.5 rounded-md px-2 py-1.5 text-base transition hover:bg-wash sm:text-sm",
                        focusRing,
                      )}
                    >
                      <item.icon
                        className="size-5 shrink-0"
                        aria-hidden="true"
                      />
                      {item.name}
                    </Link>
                  </DrawerClose>
                </li>
              ))}
            </ul>
            <div className="mt-6 space-y-1 border-t border-rule pt-4">
              <ThemeToggle />
              <DrawerClose asChild>
                <Link
                  href={siteConfig.baseLinks.styleguide}
                  className={cx(
                    "block rounded-md px-2 py-1.5 text-sm text-muted transition-colors hover:bg-wash hover:text-ink",
                    focusRing,
                  )}
                >
                  Design system
                </Link>
              </DrawerClose>
            </div>
          </nav>
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  )
}
