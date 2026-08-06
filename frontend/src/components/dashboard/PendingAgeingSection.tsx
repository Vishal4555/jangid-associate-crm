import { useEffect, useRef, useState } from "react";

import { subscribeCasesChanged } from "../../services/caseChangeEvents";
import { getPendingAgeing } from "../../services/dashboardService";
import type { PendingAgeing, PendingAgeingMetrics } from "../../types/dashboard";


const cards: Array<[keyof PendingAgeingMetrics, string, string]> = [
  ["total_pending", "Total Pending", "text-slate-900 dark:text-white"],
  ["zero_to_two", "0–2 Days", "text-emerald-600"],
  ["three_to_five", "3–5 Days", "text-amber-600"],
  ["six_to_ten", "6–10 Days", "text-orange-600"],
  ["eleven_plus", "11+ Days", "text-red-600"],
];

export default function PendingAgeingSection() {
  const [ageing, setAgeing] = useState<PendingAgeing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initializedRef = useRef(false);

  async function load(silent = false) {
    if (!silent) setLoading(true);
    try {
      setAgeing(await getPendingAgeing());
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load pending ageing.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      void load();
    }
  }, []);

  useEffect(() => subscribeCasesChanged(() => void load(true)), []);

  const tableClass = "w-full min-w-[680px] text-sm";
  const cellClass = "px-4 py-3 text-left";
  const headings = ["Name", "Total Pending", "0–2", "3–5", "6–10", "11+"];

  return (
    <section className="mt-6 space-y-4" aria-labelledby="pending-ageing-heading">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[.2em] text-orange-600">Attention needed</p>
        <h2 id="pending-ageing-heading" className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Pending Case Ageing</h2>
      </div>

      {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map(([key, label, color]) => (
          <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm font-medium text-slate-500">{label}</p>
            <p className={`mt-2 text-3xl font-bold ${color}`}>{loading ? "…" : ageing?.summary[key] ?? 0}</p>
          </article>
        ))}
      </div>

      {!loading && ageing?.summary.total_pending === 0 ? (
        <p className="rounded-2xl border border-slate-200 bg-white px-6 py-10 text-center text-slate-500 shadow-sm dark:border-slate-800 dark:bg-slate-900">No pending cases.</p>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {(["Executive", "City"] as const).map((kind) => {
            const rows = kind === "Executive"
              ? ageing?.executives.map((row) => ({ ...row, name: row.executive }))
              : ageing?.cities.map((row) => ({ ...row, name: row.city }));
            return (
              <div key={kind} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h3 className="p-5 text-lg font-semibold text-slate-900 dark:text-white">{kind}-wise Pending Ageing</h3>
                <div className="overflow-x-auto">
                  <table className={tableClass}>
                    <thead className="bg-slate-900 text-white"><tr>{headings.map((heading) => <th key={heading} className={cellClass}>{heading}</th>)}</tr></thead>
                    <tbody>{rows?.map((row) => <tr key={row.name} className="border-b border-slate-100 dark:border-slate-800"><td className={cellClass}>{row.name}</td><td className={cellClass}>{row.total_pending}</td><td className={`${cellClass} text-emerald-600`}>{row.zero_to_two}</td><td className={`${cellClass} text-amber-600`}>{row.three_to_five}</td><td className={`${cellClass} text-orange-600`}>{row.six_to_ten}</td><td className={`${cellClass} font-semibold text-red-600`}>{row.eleven_plus}</td></tr>)}</tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
