// Tremor Raw Divider [v0.0.1]

import React from "react"

import { cx } from "@/lib/utils"

type DividerProps = React.ComponentPropsWithoutRef<"div">

const Divider = React.forwardRef<HTMLDivElement, DividerProps>(
  ({ className, children, ...props }, forwardedRef) => (
    <div
      ref={forwardedRef}
      className={cx(
        // base
        "mx-auto my-6 flex w-full items-center justify-between gap-3 text-sm",
        // text color
        "text-muted",
        className,
      )}
      {...props}
    >
      {children ? (
        <>
          <div
            className={cx(
              // base
              "h-px w-full",
              // background color
              "bg-wash",
            )}
          />
          <div className="whitespace-nowrap text-inherit">{children}</div>
          <div
            className={cx(
              // base
              "h-px w-full",
              // background color
              "bg-wash",
            )}
          />
        </>
      ) : (
        <div
          className={cx(
            // base
            "h-px w-full",
            // background color
            "bg-wash",
          )}
        />
      )}
    </div>
  ),
)

Divider.displayName = "Divider"

export { Divider }
