import { useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp, Search, Inbox } from "lucide-react";

export interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => ReactNode;
  sortable?: boolean;
  sortValue?: (row: T) => string | number;
  className?: string;
}

interface Props<T> {
  columns: Column<T>[];
  data: T[];
  searchKeys?: (keyof T)[];
  emptyText?: string;
  loading?: boolean;
}

// Reusable, sortable, searchable table.
// Kept generic so /instances, /buckets, /security all share the same UX.
export default function DataTable<T extends object>({
  columns,
  data,
  searchKeys,
  emptyText = "No records found",
  loading = false,
}: Props<T>) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const filtered = useMemo(() => {
    if (!query || !searchKeys) return data;
    const q = query.toLowerCase();
    return data.filter((row) =>
      searchKeys.some((k) => {
        const v = (row as any)[k];
        return v != null && String(v).toLowerCase().includes(q);
      })
    );
  }, [data, query, searchKeys]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const col = columns.find((c) => c.key === sortKey);
    if (!col) return filtered;
    const getter =
      col.sortValue ?? ((row: T) => (row as any)[sortKey] as any);
    return [...filtered].sort((a, b) => {
      const va = getter(a);
      const vb = getter(b);
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [filtered, sortKey, sortDir, columns]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  return (
    <div className="card overflow-hidden">
      {searchKeys && (
        <div className="p-4 border-b border-white/5 flex items-center gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              className="input pl-9"
              placeholder="Search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <span className="text-xs text-slate-400">
            {sorted.length} {sorted.length === 1 ? "result" : "results"}
          </span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-ink-800/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={`table-th ${col.className ?? ""} ${
                    col.sortable ? "cursor-pointer hover:text-slate-200" : ""
                  }`}
                  onClick={() =>
                    col.sortable ? handleSort(String(col.key)) : undefined
                  }
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {col.sortable && sortKey === col.key && (
                      sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={String(c.key)} className="table-td">
                      <div className="h-3 rounded bg-white/5 animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : sorted.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-slate-500"
                >
                  <Inbox className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">{emptyText}</p>
                </td>
              </tr>
            ) : (
              sorted.map((row, i) => (
                <tr
                  key={i}
                  className="hover:bg-white/[0.02] transition-colors"
                >
                  {columns.map((col) => (
                    <td
                      key={String(col.key)}
                      className={`table-td ${col.className ?? ""}`}
                    >
                      {col.render
                        ? col.render(row)
                        : ((row as any)[col.key] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
