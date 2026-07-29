import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { getCases } from "../../services/caseService";
import type { Case } from "../../types/case";

export default function ReportsPage() {
  const [cases, setCases] = useState<Case[]>([]); const [error, setError] = useState<string | null>(null);
  useEffect(() => { void getCases().then((items) => setCases(Array.isArray(items) ? items : [])).catch((e) => setError(e instanceof Error ? e.message : "Unable to load report")); }, []);
  const counts = useMemo(() => ({ total: cases.length, pending: cases.filter((item) => item.status === "Pending").length, positive: cases.filter((item) => item.status === "Positive").length, negative: cases.filter((item) => item.status === "Negative").length }), [cases]);
  return <DashboardLayout><section className="rounded-2xl bg-white p-6 shadow"><h1 className="text-2xl font-semibold">Case report</h1>{error && <p className="mt-3 text-red-600">{error}</p>}<div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(counts).map(([label, value]) => <div key={label} className="rounded-xl border p-4"><p className="capitalize text-slate-500">{label}</p><p className="mt-1 text-3xl font-semibold">{value}</p></div>)}</div></section></DashboardLayout>;
}
