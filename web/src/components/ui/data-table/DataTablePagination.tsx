import { Button } from "@/components/Button"
import { cx } from "@/lib/utils"
import {
  RiArrowLeftDoubleLine,
  RiArrowLeftSLine,
  RiArrowRightDoubleLine,
  RiArrowRightSLine,
} from "@remixicon/react"
import { RowData, Table } from "@tanstack/react-table"
import { DataTableFeatures } from "./features"

interface DataTablePaginationProps<TData extends RowData> {
  table: Table<DataTableFeatures, TData>
  pageSize: number
}

export function DataTablePagination<TData extends RowData>({
  table,
  pageSize,
}: DataTablePaginationProps<TData>) {
  const paginationButtons = [
    {
      icon: RiArrowLeftDoubleLine,
      onClick: () => table.setPageIndex(0),
      disabled: !table.getCanPreviousPage(),
      srText: "First page",
      mobileView: "hidden sm:block",
    },
    {
      icon: RiArrowLeftSLine,
      onClick: () => table.previousPage(),
      disabled: !table.getCanPreviousPage(),
      srText: "Previous page",
      mobileView: "",
    },
    {
      icon: RiArrowRightSLine,
      onClick: () => table.nextPage(),
      disabled: !table.getCanNextPage(),
      srText: "Next page",
      mobileView: "",
    },
    {
      icon: RiArrowRightDoubleLine,
      onClick: () => table.setPageIndex(table.getPageCount() - 1),
      disabled: !table.getCanNextPage(),
      srText: "Last page",
      mobileView: "hidden sm:block",
    },
  ]

  const totalRows = table.getFilteredRowModel().rows.length
  const currentPage = table.store.state.pagination.pageIndex
  const firstRowIndex = currentPage * pageSize + 1
  const lastRowIndex = Math.min(totalRows, firstRowIndex + pageSize - 1)

  return (
    <div className="flex items-center justify-end">
      <div className="flex items-center gap-x-6 lg:gap-x-8">
        <p className="hidden text-sm text-muted tabular-nums sm:block">
          Showing{" "}
          <span className="font-medium text-ink">
            {firstRowIndex}-{lastRowIndex}
          </span>{" "}
          of <span className="font-medium text-ink">{totalRows}</span>
        </p>
        <div className="flex items-center gap-x-1.5">
          {paginationButtons.map((button, index) => (
            <Button
              key={index}
              variant="secondary"
              className={cx(button.mobileView, "p-1.5")}
              onClick={button.onClick}
              disabled={button.disabled}
            >
              <span className="sr-only">{button.srText}</span>
              <button.icon className="size-4 shrink-0" aria-hidden="true" />
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
