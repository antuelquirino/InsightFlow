import { siteConfig } from "@/app/siteConfig"
import {
  RiChat3Line,
  RiHome2Line,
  RiLineChartLine,
  RiRepeatLine,
  RiTeamLine,
} from "@remixicon/react"

// The app's sections, shared by the desktop sidebar and the mobile drawer.
export const navigation = [
  { name: "Overview", href: siteConfig.baseLinks.overview, icon: RiHome2Line },
  {
    name: "Revenue",
    href: siteConfig.baseLinks.revenue,
    icon: RiLineChartLine,
  },
  {
    name: "Retention",
    href: siteConfig.baseLinks.retention,
    icon: RiRepeatLine,
  },
  { name: "Customers", href: siteConfig.baseLinks.customers, icon: RiTeamLine },
  { name: "Ask", href: siteConfig.baseLinks.ask, icon: RiChat3Line },
] as const

export const isActive = (pathname: string, href: string) =>
  pathname === href || pathname.startsWith(`${href}/`)
