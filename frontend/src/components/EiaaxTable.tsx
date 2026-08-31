import { useCallback, useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";

export type SortDir = "asc" | "desc";

export type EiaaxColumn<T> = {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  minWidth?: number;
  /** Extraer valor para ordenar / buscar */
  getValue?: (row: T) => string | number | null | undefined;
  render?: (row: T) => ReactNode;
};

export type EiaaxTablePrefs = {
  visibleColumns: string[];
  columnWidths: Record<string, number>;
  pageSize: number;
  sortKey: string | null;
  sortDir: SortDir;
};

type Props<T> = {
  columns: EiaaxColumn<T>[];
  data: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  /** Clave localStorage para preferencias (columnas, ancho, página, orden) */
  prefsKey?: string;
  searchPlaceholder?: string;
  /** Si se omite, busca en todos los getValue/stringifiable */
  searchKeys?: string[];
  filtersSlot?: ReactNode;
  toolbarSlot?: ReactNode;
  pageSizeOptions?: number[];
  defaultPageSize?: number;
  defaultSortKey?: string;
  defaultSortDir?: SortDir;
  className?: string;
  onRowClick?: (row: T) => void;
};

const DEFAULT_PAGE_SIZES = [10, 25, 50, 100];

function loadPrefs(key: string | undefined, columns: EiaaxColumn<unknown>[], defaultPageSize: number): EiaaxTablePrefs {
  const allKeys = columns.map((c) => c.key);
  const fallback: EiaaxTablePrefs = {
    visibleColumns: allKeys,
    columnWidths: {},
    pageSize: defaultPageSize,
    sortKey: null,
    sortDir: "asc",
  };
  if (!key) return fallback;
  try {
    const raw = localStorage.getItem(`eiaax_table_${key}`);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as Partial<EiaaxTablePrefs>;
    return {
      visibleColumns: (parsed.visibleColumns ?? allKeys).filter((k) => allKeys.includes(k)),
      columnWidths: parsed.columnWidths ?? {},
      pageSize: parsed.pageSize ?? defaultPageSize,
      sortKey: parsed.sortKey ?? null,
      sortDir: parsed.sortDir ?? "asc",
    };
  } catch {
    return fallback;
  }
}

function cellText<T>(row: T, col: EiaaxColumn<T>): string {
  const v = col.getValue ? col.getValue(row) : (row as Record<string, unknown>)[col.key];
  if (v == null) return "";
  return String(v);
}

export function EiaaxTable<T>({
  columns,
  data,
  rowKey,
  loading = false,
  emptyMessage = "Sin registros",
  prefsKey,
  searchPlaceholder = "Buscar…",
  searchKeys,
  filtersSlot,
  toolbarSlot,
  pageSizeOptions = DEFAULT_PAGE_SIZES,
  defaultPageSize = 25,
  defaultSortKey,
  defaultSortDir = "asc",
  className = "",
  onRowClick,
}: Props<T>) {
  const [search, setSearch] = useState("");
  const [prefs, setPrefs] = useState<EiaaxTablePrefs>(() =>
    loadPrefs(prefsKey, columns as EiaaxColumn<unknown>[], defaultPageSize),
  );
  const [showCols, setShowCols] = useState(false);
  const [page, setPage] = useState(0);
  const [resizing, setResizing] = useState<{ key: string; startX: number; startW: number } | null>(null);

  useEffect(() => {
    if (!prefsKey) return;
    localStorage.setItem(`eiaax_table_${prefsKey}`, JSON.stringify(prefs));
  }, [prefs, prefsKey]);

  const visibleColumns = useMemo(
    () => columns.filter((c) => prefs.visibleColumns.includes(c.key)),
    [columns, prefs.visibleColumns],
  );

  const sortKey = prefs.sortKey ?? defaultSortKey ?? null;
  const sortDir = prefs.sortKey ? prefs.sortDir : defaultSortDir;

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let rows = [...data];
    if (q) {
      const keys = searchKeys ?? columns.map((c) => c.key);
      rows = rows.filter((row) =>
        keys.some((key) => {
          const col = columns.find((c) => c.key === key);
          if (!col) return false;
          return cellText(row, col).toLowerCase().includes(q);
        }),
      );
    }
    if (sortKey) {
      const col = columns.find((c) => c.key === sortKey);
      if (col) {
        rows.sort((a, b) => {
          const av = cellText(a, col);
          const bv = cellText(b, col);
          const cmp = av.localeCompare(bv, "es", { numeric: true, sensitivity: "base" });
          return sortDir === "asc" ? cmp : -cmp;
        });
      }
    }
    return rows;
  }, [data, search, searchKeys, columns, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / prefs.pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = filtered.slice(safePage * prefs.pageSize, (safePage + 1) * prefs.pageSize);

  useEffect(() => {
    if (page !== safePage) setPage(safePage);
  }, [safePage, page]);

  const toggleSort = useCallback((key: string) => {
    setPrefs((p) => {
      if (p.sortKey === key) {
        return { ...p, sortDir: p.sortDir === "asc" ? "desc" : "asc" };
      }
      return { ...p, sortKey: key, sortDir: "asc" };
    });
  }, []);

  const toggleColumn = useCallback((key: string) => {
    setPrefs((p) => {
      const has = p.visibleColumns.includes(key);
      const next = has ? p.visibleColumns.filter((k) => k !== key) : [...p.visibleColumns, key];
      if (next.length === 0) return p;
      return { ...p, visibleColumns: next };
    });
  }, []);

  useEffect(() => {
    if (!resizing) return;
    function onMove(e: MouseEvent) {
      const delta = e.clientX - resizing.startX;
      const w = Math.max(60, resizing.startW + delta);
      setPrefs((p) => ({
        ...p,
        columnWidths: { ...p.columnWidths, [resizing.key]: w },
      }));
    }
    function onUp() {
      setResizing(null);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [resizing]);

  return (
    <div className={`eiaax-table ${className}`.trim()}>
      <div className="eiaax-table-toolbar filters-row">
        <input
          type="search"
          placeholder={searchPlaceholder}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          aria-label="Buscar en tabla"
        />
        {filtersSlot}
        <div className="eiaax-table-toolbar-actions">
          {toolbarSlot}
          <div className="eiaax-table-cols-picker">
            <button type="button" className="btn small" onClick={() => setShowCols((v) => !v)}>
              Columnas
            </button>
            {showCols && (
              <div className="eiaax-table-cols-menu" role="menu">
                {columns.map((col) => (
                  <label key={col.key} className="checkbox-inline">
                    <input
                      type="checkbox"
                      checked={prefs.visibleColumns.includes(col.key)}
                      onChange={() => toggleColumn(col.key)}
                    />
                    {col.label}
                  </label>
                ))}
              </div>
            )}
          </div>
          <label className="eiaax-table-page-size">
            <span className="muted">Filas</span>
            <select
              value={prefs.pageSize}
              onChange={(e) => {
                setPrefs((p) => ({ ...p, pageSize: Number(e.target.value) }));
                setPage(0);
              }}
            >
              {pageSizeOptions.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <p className="muted eiaax-table-summary">
        {loading ? "Cargando…" : `${filtered.length} registro(s)`}
        {filtered.length !== data.length && ` · filtrados de ${data.length}`}
      </p>

      <div className="table-wrap">
        <table className="data-table compact-table eiaax-data-table">
          <thead>
            <tr>
              {visibleColumns.map((col) => {
                const w = prefs.columnWidths[col.key] ?? col.width;
                const style: CSSProperties = {};
                if (w) style.width = typeof w === "number" ? `${w}px` : w;
                if (col.minWidth) style.minWidth = col.minWidth;
                return (
                  <th key={col.key} style={style}>
                    {col.sortable !== false ? (
                      <button
                        type="button"
                        className={`sort-btn ${sortKey === col.key ? `sort-${sortDir}` : ""}`}
                        onClick={() => toggleSort(col.key)}
                      >
                        {col.label}
                        {sortKey === col.key && (sortDir === "asc" ? " ▲" : " ▼")}
                      </button>
                    ) : (
                      col.label
                    )}
                    <span
                      className="col-resize-handle"
                      role="separator"
                      aria-orientation="vertical"
                      onMouseDown={(e) => {
                        const th = (e.target as HTMLElement).closest("th");
                        const startW = th?.getBoundingClientRect().width ?? 120;
                        setResizing({ key: col.key, startX: e.clientX, startW });
                      }}
                    />
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {!loading && pageRows.length === 0 && (
              <tr>
                <td colSpan={visibleColumns.length} className="muted">
                  {emptyMessage}
                </td>
              </tr>
            )}
            {pageRows.map((row) => (
              <tr
                key={rowKey(row)}
                className={onRowClick ? "eiaax-table-row-clickable" : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {visibleColumns.map((col) => (
                  <td key={col.key} style={prefs.columnWidths[col.key] ? { maxWidth: prefs.columnWidths[col.key] } : undefined}>
                    {col.render ? col.render(row) : cellText(row, col) || "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="eiaax-table-pagination">
          <button type="button" className="btn small" disabled={safePage === 0} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </button>
          <span className="muted">
            Página {safePage + 1} de {totalPages}
          </span>
          <button
            type="button"
            className="btn small"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
}
