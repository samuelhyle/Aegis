"use client";

import React, { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { Input } from "./Input";
import { Skeleton } from "./Skeleton";
import { ChevronDown, ChevronUp, ChevronsUpDown, Search, ChevronLeft, ChevronRight } from "lucide-react";

export interface Column<T> {
  id: string;
  header: string | React.ReactNode;
  accessorKey?: keyof T;
  accessorFn?: (row: T) => unknown;
  cell?: (row: T) => React.ReactNode;
  sortable?: boolean;
  sortFn?: (a: T, b: T) => number;
  className?: string;
  headerClassName?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchAccessor?: keyof T;
  pagination?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  className?: string;
  headerClassName?: string;
  rowClassName?: string | ((row: T) => string);
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  searchable = false,
  searchPlaceholder = "Search...",
  searchAccessor,
  pagination = false,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [10, 20, 50],
  onRowClick,
  emptyMessage = "No data available",
  className,
  headerClassName,
  rowClassName,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("");
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: "asc" | "desc" } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const filteredData = useMemo(() => {
    if (!search || !searchAccessor) return data;

    return data.filter((row) => {
      const value = row[searchAccessor];
      return String(value).toLowerCase().includes(search.toLowerCase());
    });
  }, [data, search, searchAccessor]);

  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData;

    return [...filteredData].sort((a, b) => {
      const column = columns.find((col) => col.id === sortConfig.key);
      if (!column) return 0;

      let valueA: string | number | boolean | Date | null = null;
      let valueB: string | number | boolean | Date | null = null;

      if (column.accessorFn) {
        const rawA = column.accessorFn(a);
        const rawB = column.accessorFn(b);
        valueA = rawA as string | number | boolean | Date | null;
        valueB = rawB as string | number | boolean | Date | null;
      } else if (column.accessorKey) {
        valueA = a[column.accessorKey] as string | number | boolean | Date | null;
        valueB = b[column.accessorKey] as string | number | boolean | Date | null;
      } else {
        return 0;
      }

      if (column.sortFn) {
        return sortConfig.direction === "asc" ? column.sortFn(a, b) : column.sortFn(b, a);
      }

      if (valueA === null || valueA === undefined) return 1;
      if (valueB === null || valueB === undefined) return -1;
      if (valueA < valueB) return sortConfig.direction === "asc" ? -1 : 1;
      if (valueA > valueB) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortConfig, columns]);

  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData;

    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, pagination, currentPage, pageSize]);

  const totalPages = useMemo(() => {
    if (!pagination) return 1;
    return Math.ceil(sortedData.length / pageSize);
  }, [sortedData.length, pageSize, pagination]);

  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return;

    setSortConfig((current) => {
      if (current?.key === column.id) {
        if (current.direction === "asc") {
          return { key: column.id, direction: "desc" };
        }
        return null;
      }
      return { key: column.id, direction: "asc" };
    });
  };

  const getSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null;

    if (sortConfig?.key === column.id) {
      return sortConfig.direction === "asc" ? (
        <ChevronUp className="h-4 w-4" />
      ) : (
        <ChevronDown className="h-4 w-4" />
      );
    }

    return <ChevronsUpDown className="h-4 w-4 opacity-50" />;
  };

  const getCellValue = (row: T, column: Column<T>): React.ReactNode => {
    if (column.cell) {
      return column.cell(row);
    }

    if (column.accessorFn) {
      return column.accessorFn(row) as React.ReactNode;
    }

    if (column.accessorKey) {
      return row[column.accessorKey] as React.ReactNode;
    }

    return null;
  };

  const getRowClassName = (row: T) => {
    if (typeof rowClassName === "function") {
      return rowClassName(row);
    }
    return rowClassName;
  };

  if (loading) {
    return (
      <div className={cn("w-full", className)}>
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      {searchable && (
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
            <Input
              placeholder={searchPlaceholder}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-10"
            />
          </div>
        </div>
      )}

      <div className="rounded-md border border-neutral-200 dark:border-neutral-800">
        <div className="overflow-x-auto">
          <table className="w-full caption-bottom text-sm">
            <thead className={cn("[&_tr]:border-b", headerClassName)}>
              <tr className="border-b border-neutral-200 transition-colors hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-800/50">
                {columns.map((column) => (
                  <th
                    key={column.id}
                    className={cn(
                      "h-12 px-4 text-left align-middle font-medium text-neutral-500 dark:text-neutral-400",
                      column.sortable && "cursor-pointer select-none hover:text-neutral-900 dark:hover:text-neutral-100",
                      column.headerClassName
                    )}
                    onClick={() => handleSort(column)}
                  >
                    <div className="flex items-center gap-2">
                      {column.header}
                      {getSortIcon(column)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {paginatedData.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="h-24 text-center text-neutral-500 dark:text-neutral-400"
                  >
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className={cn(
                      "border-b border-neutral-200 transition-colors hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-800/50",
                      onRowClick && "cursor-pointer",
                      getRowClassName(row)
                    )}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <td key={column.id} className={cn("p-4 align-middle", column.className)}>
                        {getCellValue(row, column)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {pagination && totalPages > 1 && (
        <div className="flex items-center justify-between px-2 py-4">
          <div className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="h-8 rounded-md border border-neutral-200 bg-transparent px-2 text-sm dark:border-neutral-800"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
            <span>
              {filteredData.length === 0
                ? "0"
                : `${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, filteredData.length)}`}{" "}
              of {filteredData.length}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((page) => {
                const distance = Math.abs(page - currentPage);
                return distance <= 2 || page === 1 || page === totalPages;
              })
              .map((page, index, array) => (
                <React.Fragment key={page}>
                  {index > 0 && array[index - 1] !== page - 1 && (
                    <span className="px-2 text-neutral-500">...</span>
                  )}
                  <Button
                    variant={currentPage === page ? "default" : "outline"}
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </Button>
                </React.Fragment>
              ))}
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export function DataTableColumnHeader<T>({
  column,
  className,
}: {
  column: Column<T>;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {column.header}
      {column.sortable && <ChevronsUpDown className="h-4 w-4 opacity-50" />}
    </div>
  );
}
