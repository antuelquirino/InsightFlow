// The design tokens as data, for the /styleguide page. globals.css is the
// source of truth; tokens.test.ts fails if these values drift from it.

export interface ColorToken {
  name: string
  variable: string // CSS custom property, without the leading --
  role: string
  light: string
  dark: string
}

export const INTERFACE_COLORS: ColorToken[] = [
  {
    name: "Paper",
    variable: "paper",
    role: "Page background",
    light: "#f5f3ee",
    dark: "#1a1916",
  },
  {
    name: "Surface",
    variable: "surface",
    role: "Panels, charts and inputs",
    light: "#fdfcf9",
    dark: "#24221e",
  },
  {
    name: "Ink",
    variable: "ink",
    role: "Primary text",
    light: "#1f1d19",
    dark: "#f2eee6",
  },
  {
    name: "Graphite",
    variable: "graphite",
    role: "Secondary text",
    light: "#5b564c",
    dark: "#bbb3a4",
  },
  {
    name: "Muted",
    variable: "muted",
    role: "Axes and captions",
    light: "#726c60",
    dark: "#968f81",
  },
  {
    name: "Rule",
    variable: "rule",
    role: "Hairlines and borders",
    light: "#e3dfd4",
    dark: "#3a3731",
  },
  {
    name: "Ochre",
    variable: "ochre",
    role: "The accent: what to look at",
    light: "#a86422",
    dark: "#d57c11",
  },
  {
    name: "Highlight",
    variable: "highlight",
    role: "The marker behind a key figure",
    light: "#f6dfb0",
    dark: "#5a3d12",
  },
  {
    name: "Gain",
    variable: "gain",
    role: "Only for “improves”",
    light: "#1b7342",
    dark: "#5cc48a",
  },
  {
    name: "Loss",
    variable: "loss",
    role: "Only for “worsens”",
    light: "#b3372a",
    dark: "#f07a67",
  },
]

export const SERIES_COLORS: ColorToken[] = [
  {
    name: "Series 1 · Ochre",
    variable: "series-1",
    role: "Starter · Organic",
    light: "#a86422",
    dark: "#d57c11",
  },
  {
    name: "Series 2 · Teal",
    variable: "series-2",
    role: "Pro · Paid ads",
    light: "#1a9aa0",
    dark: "#1faaa4",
  },
  {
    name: "Series 3 · Plum",
    variable: "series-3",
    role: "Enterprise · Partner",
    light: "#8e3c89",
    dark: "#a947a3",
  },
  {
    name: "Series 4 · Blue",
    variable: "series-4",
    role: "Outbound",
    light: "#4f7fd4",
    dark: "#3c8ff4",
  },
  {
    name: "Context",
    variable: "series-muted",
    role: "Series next to the highlighted one",
    light: "#b7b0a2",
    dark: "#5d584f",
  },
]
