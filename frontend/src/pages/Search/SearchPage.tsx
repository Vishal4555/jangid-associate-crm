import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { getCases } from "../../services/caseService";
import type { Case } from "../../types/case";

export default function SearchPage() {
  const [cases, setCases] = useState<Case[]>([]); const [query, setQuery] = useState(""); const [error, setError] = useState<string | null>(null);
  useEffect(() => { void getCases().then((items) => setCases(Array.isArray(items) ? items : [])).catch((e) => setError(e instanceof Error ? e.message : "Unable to search cases")); }, []);
  const results = useMemo(() => { const term = query.trim().toLowerCase(); return !term ? cases : cases.filter((item) => [item.case_no, item.applicant, item.mobile, item.bank, item.city].join(" ").toLowerCase().includes(term)); }, [cases, query]);
  return <DashboardLayout><section className="rounded-2xl bg-white p-6 shadow"><h1 className="text-2xl font-semibold">Search cases</h1><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Case number, applicant, mobile, bank, or city" className="mt-4 w-full rounded-lg border p-3" />{error && <p className="mt-3 text-red-600">{error}</p>}<p className="mt-4 text-sm text-slate-500">{results.length} result(s)</p><div className="mt-3 divide-y">{results.map((item) => <div key={item.id} className="py-3"><strong>{item.case_no}</strong> Â· {item.applicant || "Unknown applicant"}<span className="ml-3 text-slate-500">{item.bank} Â· {item.status}</span></div>)}{results.length === 0 && <p className="py-5 text-slate-500">No matching cases.</p>}</div></section></DashboardLayout>;
}
