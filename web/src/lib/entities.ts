import type { AvailableChartColorsKeys } from "./chartUtils"
import type { Channel, Plan } from "./types"

// Each entity keeps its color on every screen: a filter never repaints it.
// Slots follow the validated series order (ochre, teal, plum, blue).

export const PLANS: Plan[] = ["starter", "pro", "enterprise"]
export const CHANNELS: Channel[] = [
  "organic",
  "paid_ads",
  "partner",
  "outbound",
]

export const PLAN_LABELS: Record<Plan, string> = {
  starter: "Starter",
  pro: "Pro",
  enterprise: "Enterprise",
}

export const CHANNEL_LABELS: Record<Channel, string> = {
  organic: "Organic",
  paid_ads: "Paid ads",
  partner: "Partner",
  outbound: "Outbound",
}

export const PLAN_COLORS: Record<Plan, AvailableChartColorsKeys> = {
  starter: "ochre",
  pro: "teal",
  enterprise: "plum",
}

export const CHANNEL_COLORS: Record<Channel, AvailableChartColorsKeys> = {
  organic: "ochre",
  paid_ads: "teal",
  partner: "plum",
  outbound: "blue",
}
