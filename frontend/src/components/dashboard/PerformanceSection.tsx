import { type FormEvent, useEffect, useRef, useState } from "react";
import * as XLSX from "xlsx";

import { subscribeCasesChanged } from "../../services/caseChangeEvents";
import { getDashboardPerformance } from "../../services/dashboardService";
import type { DashboardPerformance, PerformanceFilters } from "../../types/dashboard";

const EMPTY_FILTERS: PerformanceFilters = {
  from_date: "",
  to_date: "",
  executive: "",
  city: "",
  bank: "",
};

type FilterOptions = {
  executives: string[];
  cities: string[];
  banks: string[];
};

function formatTat(value: number | null): string {
  return value === null ? "-" : `${value} days`;
}

function cleanFilters(filters: PerformanceFilters): PerformanceFilters {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value?.trim()),
  );
}

function setColumnWidths(sheet: XLSX.WorkSheet, widths: number[]) {
  sheet["!cols"] = widths.map((wch) => ({ wch }));
}

export default function PerformanceSection() {
  const [performance, setPerformance] = useState<DashboardPerformance | null>(null);
  const [draftFilters, setDraftFilters] = useState<PerformanceFilters>(EMPTY_FILTERS);
  const [activeFilters, setActiveFilters] = useState<PerformanceFilters>({});
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    executives: [],
    cities: [],
    banks: [],
  });
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initializedRef = useRef(false);

  async function load(filters: PerformanceFilters, silent = false) {
    if (!silent) setLoading(true);
    try {
      const result = await getDashboardPerformance(filters);
      setPerformance(result);
      if (Object.keys(filters).length === 0) {
        setFilterOptions({
          executives: result.executives.map((row) => row.executive_name).filter((name) => name !== "Unassigned"),
          cities: result.cities.map((row) => row.city).filter((name) => name !== "Unassigned"),
          banks: result.banks.map((row) => row.bank).filter((name) => name !== "Unassigned"),
        });
      }
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load performance data.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      void load({});
    }
  }, []);

  useEffect(
    () => subscribeCasesChanged(() => void load(activeFilters, true)),
    [activeFilters],
  );

  function updateFilter(key: keyof PerformanceFilters, value: string) {
    setDraftFilters((current) => ({ ...current, [key]: value }));
  }

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const filters = cleanFilters(draftFilters);
    setActiveFilters(filters);
    void load(filters);
  }

  function clearFilters() {
    setDraftFilters(EMPTY_FILTERS);
    setActiveFilters({});
    void load({});
  }

  const summary = performance?.summary;
  const fastestValues = performance?.executives
    .map((row) => row.fastest_tat)
    .filter((value): value is number => value !== null) ?? [];
  const slowestValues = performance?.executives
    .map((row) => row.slowest_tat)
    .filter((value): value is number => value !== null) ?? [];
  const fastestTat = fastestValues.length > 0 ? Math.min(...fastestValues) : null;
  const slowestTat = slowestValues.length > 0 ? Math.max(...slowestValues) : null;
  const hasData = (summary?.total_cases ?? 0) > 0;
  const cards = [
    ["Total Cases", summary?.total_cases ?? 0],
    ["Pending", summary?.pending_cases ?? 0],
    ["Positive", summary?.positive_cases ?? 0],
    ["Negative", summary?.negative_cases ?? 0],
    ["Closed", summary?.closed_cases ?? 0],
    ["Average TAT", summary ? formatTat(summary.average_tat) : "-"],
    ["Fastest TAT", formatTat(fastestTat)],
    ["Slowest TAT", formatTat(slowestTat)],
  ];

  const tableClass = "w-full min-w-[760px] text-sm";
  const headerClass = "bg-slate-900 text-left text-white";
  const cellClass = "px-4 py-3";

  function exportExcel() {
    if (!performance || !hasData) return;

    setExporting(true);
    try {
      const summarySheet = XLSX.utils.aoa_to_sheet([
        ["Metric", "Value"],
        ["Total Cases", performance.summary.total_cases],
        ["Pending", performance.summary.pending_cases],
        ["Positive", performance.summary.positive_cases],
        ["Negative", performance.summary.negative_cases],
        ["Closed", performance.summary.closed_cases],
        ["Average TAT", performance.summary.average_tat ?? "-"],
        ["Fastest TAT", fastestTat ?? "-"],
        ["Slowest TAT", slowestTat ?? "-"],
        ["From Date", activeFilters.from_date || "All dates"],
        ["To Date", activeFilters.to_date || "All dates"],
        ["Executive", activeFilters.executive || "All Executives"],
        ["City", activeFilters.city || "All Cities"],
        ["Bank", activeFilters.bank || "All Banks"],
      ]);
      setColumnWidths(summarySheet, [24, 24]);

      const executiveSheet = XLSX.utils.json_to_sheet(
        performance.executives.map((row) => ({
          Executive: row.executive_name,
          Total: row.total_cases,
          Pending: row.pending,
          Positive: row.positive,
          Negative: row.negative,
          Closed: row.closed,
          "Average TAT": row.average_tat ?? "-",
          Fastest: row.fastest_tat ?? "-",
          Slowest: row.slowest_tat ?? "-",
        })),
      );
      setColumnWidths(executiveSheet, [24, 10, 10, 10, 10, 10, 15, 12, 12]);

      const citySheet = XLSX.utils.json_to_sheet(
        performance.cities.map((row) => ({
          City: row.city,
          Total: row.total_cases,
          Pending: row.pending,
          Positive: row.positive,
          Negative: row.negative,
          "Average TAT": row.average_tat ?? "-",
        })),
      );
      setColumnWidths(citySheet, [24, 10, 10, 10, 10, 15]);

      const bankSheet = XLSX.utils.json_to_sheet(
        performance.banks.map((row) => ({
          Bank: row.bank,
          Total: row.total_cases,
          Pending: row.pending,
          Positive: row.positive,
          Negative: row.negative,
          "Average TAT": row.average_tat ?? "-",
        })),
      );
      setColumnWidths(bankSheet, [28, 10, 10, 10, 10, 15]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, summarySheet, "Summary");
      XLSX.utils.book_append_sheet(workbook, executiveSheet, "Executive Performance");
      XLSX.utils.book_append_sheet(workbook, citySheet, "City Performance");
      XLSX.utils.book_append_sheet(workbook, bankSheet, "Bank Performance");
      XLSX.writeFile(
        workbook,
        `jangid-associate-report-${new Date().toISOString().slice(0, 10)}.xlsx`,
        { compression: true },
      );
    } finally {
      setExporting(false);
    }
  }

  return (
    <section className="space-y-6" aria-labelledby="performance-heading">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[.2em] text-orange-600">Performance</p>
        <h2 id="performance-heading" className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
          Executive Performance
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Case outcomes and turnaround time by executive, city, and bank.
        </p>
      </div>

      <form
        onSubmit={applyFilters}
        className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 xl:grid-cols-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <input type="date" aria-label="From date" value={draftFilters.from_date ?? ""} onChange={(event) => updateFilter("from_date", event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800" />
        <input type="date" aria-label="To date" value={draftFilters.to_date ?? ""} onChange={(event) => updateFilter("to_date", event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800" />
        <select aria-label="Executive" value={draftFilters.executive ?? ""} onChange={(event) => updateFilter("executive", event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"><option value="">All executives</option>{filterOptions.executives.map((name) => <option key={name} value={name}>{name}</option>)}</select>
        <select aria-label="City" value={draftFilters.city ?? ""} onChange={(event) => updateFilter("city", event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"><option value="">All cities</option>{filterOptions.cities.map((name) => <option key={name} value={name}>{name}</option>)}</select>
        <select aria-label="Bank" value={draftFilters.bank ?? ""} onChange={(event) => updateFilter("bank", event.target.value)} className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"><option value="">All banks</option>{filterOptions.banks.map((name) => <option key={name} value={name}>{name}</option>)}</select>
        <button type="submit" className="rounded-xl bg-orange-600 px-4 py-2 font-medium text-white hover:bg-orange-700">Apply</button>
        <button type="button" onClick={clearFilters} className="rounded-xl border border-slate-200 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800">Clear</button>
        <button type="button" onClick={exportExcel} disabled={!hasData || loading || exporting} className="rounded-xl border border-orange-200 bg-orange-50 px-4 py-2 font-medium text-orange-700 hover:bg-orange-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-orange-900 dark:bg-orange-500/10 dark:text-orange-300">{exporting ? "Exporting…" : "Export Excel"}</button>
      </form>

      {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <article key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm font-medium text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{loading ? "…" : value}</p>
          </article>
        ))}
      </div>

      {!loading && !hasData && (
        <p className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          No report data matches the selected filters.
        </p>
      )}

      {hasData && <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="p-5 text-lg font-semibold text-slate-900 dark:text-white">Executive Performance</h3>
        <div className="overflow-x-auto">
          <table className={tableClass}>
            <thead className={headerClass}><tr>{["Executive", "Total", "Pending", "Positive", "Negative", "Closed", "Average TAT", "Fastest", "Slowest"].map((heading) => <th key={heading} className={cellClass}>{heading}</th>)}</tr></thead>
            <tbody>{performance?.executives.map((row) => <tr key={row.executive_name} className="border-b border-slate-100 dark:border-slate-800"><td className={cellClass}>{row.executive_name}</td><td className={cellClass}>{row.total_cases}</td><td className={cellClass}>{row.pending}</td><td className={cellClass}>{row.positive}</td><td className={cellClass}>{row.negative}</td><td className={cellClass}>{row.closed}</td><td className={cellClass}>{formatTat(row.average_tat)}</td><td className={cellClass}>{formatTat(row.fastest_tat)}</td><td className={cellClass}>{formatTat(row.slowest_tat)}</td></tr>)}</tbody>
          </table>
        </div>
      </div>}

      {hasData && (["City", "Bank"] as const).map((kind) => {
        const rows = kind === "City"
          ? performance?.cities.map((row) => ({ ...row, name: row.city }))
          : performance?.banks.map((row) => ({ ...row, name: row.bank }));
        return <div key={kind} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"><h3 className="p-5 text-lg font-semibold text-slate-900 dark:text-white">{kind} Performance</h3><div className="overflow-x-auto"><table className={tableClass}><thead className={headerClass}><tr>{[kind, "Total", "Pending", "Positive", "Negative", "Average TAT"].map((heading) => <th key={heading} className={cellClass}>{heading}</th>)}</tr></thead><tbody>{rows?.map((row) => <tr key={row.name} className="border-b border-slate-100 dark:border-slate-800"><td className={cellClass}>{row.name}</td><td className={cellClass}>{row.total_cases}</td><td className={cellClass}>{row.pending}</td><td className={cellClass}>{row.positive}</td><td className={cellClass}>{row.negative}</td><td className={cellClass}>{formatTat(row.average_tat)}</td></tr>)}</tbody></table></div></div>;
      })}
    </section>
  );
}
