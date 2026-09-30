// Tremor Raw Input [v1.0.0]

import { RiSearchLine } from "@remixicon/react"
import * as React from "react"
import { tv, type VariantProps } from "tailwind-variants"

import { cx, focusInput, hasErrorInput } from "@/lib/utils"

const inputStyles = tv({
  base: [
    // base
    "relative block w-full appearance-none rounded-md border px-2.5 py-1.5 outline-hidden transition sm:text-sm",
    // border color (border only used in dark mode for better aesthetics in filterbar)
    "border-transparent",
    // text color
    "text-ink",
    // placeholder color
    "placeholder-gray-400",
    // background color
    "bg-wash",
    // disabled
    "disabled:border-rule disabled:bg-wash disabled:text-muted",
    "",
    // focus
    focusInput,
    // invalid (optional)
    // " aria-invalid:ring-2 aria-invalid:ring-loss/20 aria-invalid:border-loss invalid:ring-2 invalid:ring-loss/20 invalid:border-loss"
    // remove search cancel button (optional)
    "[&::--webkit-search-cancel-button]:hidden [&::-webkit-search-cancel-button]:hidden [&::-webkit-search-decoration]:hidden",
  ],
  variants: {
    hasError: {
      true: hasErrorInput,
    },
    // number input
    enableStepper: {
      true: "[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none",
    },
  },
})

interface InputProps
  extends
    React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputStyles> {
  inputClassName?: string
}

const Searchbar = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      inputClassName,
      hasError,
      enableStepper,
      type = "search",
      ...props
    }: InputProps,
    forwardedRef,
  ) => {
    return (
      <div className={cx("relative w-full", className)}>
        <input
          ref={forwardedRef}
          type={type}
          className={cx(
            inputStyles({ hasError, enableStepper }),
            "pl-8",
            inputClassName,
          )}
          {...props}
        />
        <div
          className={cx(
            // base
            "pointer-events-none absolute bottom-0 left-2 flex h-full items-center justify-center",
            // text color
            "text-muted",
          )}
        >
          <RiSearchLine className="size-4.5 shrink-0" aria-hidden="true" />
        </div>
      </div>
    )
  },
)

Searchbar.displayName = "Searchbar"

export { Searchbar }
