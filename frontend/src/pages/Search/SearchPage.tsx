import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { Alert, Card, EmptyState, PageHeader } from "../../components/ui";
import { getCases } from "../../services/caseService";
import type { Case } from "../../types/case";

export default function SearchPage() {
  const [cases, setCases] = useState<Case[]>([]); const [query, setQuery] = useState(""); const [error, setError] = useState<string | null>(null);
  useEffect(() => { void getCases().then((items) => setCases(Array.isArray(items) ? items : [])).catch((e) => setError(e instanceof Error ? e.message : "Unable to search cases")); }, []);
  const results = useMemo(() => { const term = query.trim().toLowerCase(); return !term ? cases : cases.filter((item) => [item.los_no, item.case_no, item.applicant, item.mobile, item.bank, item.city].join(" ").toLowerCase().includes(term)); }, [cases, query]);
  return <DashboardLayout><PageHeader eyebrow="Cases" title="Search cases" subtitle="Find a case by LOS number, applicant, mobile, bank, or city." />
    <Card>
      <input aria-label="Search cases" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="LOS / Application No, applicant, mobile, bank, or city" className="w-full border px-3 py-2" />
      {error && <Alert className="mt-3">{error}</Alert>}
      <p className="mt-3 text-sm text-slate-500">{results.length} result(s)</p>
      <div className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">{results.map((item) => <div key={item.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-3"><strong>{item.los_no || "Not available"}</strong><span>{item.applicant || "Unknown applicant"}</span><span className="text-slate-500">{item.bank} · {item.status}</span></div>)}{results.length === 0 && <EmptyState>No matching cases.</EmptyState>}</div>
    </Card>
  </DashboardLayout>;
}
