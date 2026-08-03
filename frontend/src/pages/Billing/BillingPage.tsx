import { Pencil, Plus } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import * as XLSX from "xlsx";

import BillingModal from "../../components/billing/BillingModal";
import BulkBillingModal from "../../components/billing/BulkBillingModal";
import DashboardLayout from "../../layouts/DashboardLayout";
import { createBilling, getBilling, updateBilling } from "../../services/billingService";
import { getCases } from "../../services/caseService";
import type { BillingFilters, BillingPayload, BillingRecord, PaymentStatus } from "../../types/billing";
import type { Case } from "../../types/case";


const paymentStatuses: PaymentStatus[] = ["Pending", "Partially Paid", "Paid", "Cancelled"];
const money = (value: string | number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Number(value) || 0);
const clean = (filters: BillingFilters) => Object.fromEntries(Object.entries(filters).filter(([, value]) => value)) as BillingFilters;
const today = () => new Date().toISOString().slice(0, 10);

export default function BillingPage() {
  const [records, setRecords] = useState<BillingRecord[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [billedCaseIds, setBilledCaseIds] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState<BillingFilters>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<BillingRecord | null>(null);
  const [bulkOpen, setBulkOpen] = useState(false);
  const initialized = useRef(false);

  async function load(active: BillingFilters = {}) {
    setLoading(true);
    try {
      const [billing, caseItems, allBilling] = await Promise.all([getBilling(clean(active)), getCases(), getBilling()]);
      setRecords(billing);
      setCases(caseItems);
      setBilledCaseIds(new Set(allBilling.map((record) => record.case_id)));
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load billing.");
    } finally { setLoading(false); }
  }

  useEffect(() => { if (!initialized.current) { initialized.current = true; void load(); } }, []);
  const setFilter = (key: keyof BillingFilters, value: string) => setFilters((current) => ({ ...current, [key]: value || undefined }));
  const availableCases = cases.filter((item) => editing?.case_id === item.id || !billedCaseIds.has(item.id));
  const options = useMemo(() => ({ banks: [...new Set(cases.map((item) => item.bank).filter(Boolean))], executives: [...new Set(cases.map((item) => item.executive).filter(Boolean))], cities: [...new Set(cases.map((item) => item.city).filter(Boolean))] }), [cases]);
  const total = (field: keyof BillingRecord) => records.reduce((sum, record) => sum + Number(record[field]), 0);
  const cards = [["Total Bank Payout", total("bank_payout_amount")], ["Bank Received", total("bank_paid_amount")], ["Bank Outstanding", total("bank_balance")], ["Total Executive Payout", total("executive_payout_amount")], ["Executive Paid", total("executive_paid_amount")], ["Executive Outstanding", total("executive_balance")], ["Expected Gross Margin", total("expected_gross_margin")], ["Realized Cash Margin", total("realized_cash_margin")]] as const;

  async function save(payload: BillingPayload) { if (editing) await updateBilling(editing.id, payload); else await createBilling(payload); setModalOpen(false); setEditing(null); await load(filters); }
  function openEdit(record: BillingRecord) { setEditing(record); setModalOpen(true); }

  function exportSheet(kind: "all" | "bank" | "executive") {
    if (!records.length) return;
    const rows = records.map((r) => kind === "all" ? { "Case No": r.case_no, Applicant: r.applicant ?? "", Bank: r.bank ?? "", City: r.city ?? "", Executive: r.executive ?? "", "Bank Payout": Number(r.bank_payout_amount), "Bank Received": Number(r.bank_paid_amount), "Bank Balance": Number(r.bank_balance), "Bank Status": r.bank_payment_status, "Bank Paid Date": r.bank_paid_date ?? "", "Bank Reference": r.bank_payment_reference ?? "", "Executive Payout": Number(r.executive_payout_amount), "Executive Paid": Number(r.executive_paid_amount), "Executive Balance": Number(r.executive_balance), "Executive Status": r.executive_payment_status, "Executive Paid Date": r.executive_paid_date ?? "", "Executive Reference": r.executive_payment_reference ?? "", "Expected Gross Margin": Number(r.expected_gross_margin), "Realized Cash Margin": Number(r.realized_cash_margin), Remarks: r.remarks ?? "" } : kind === "bank" ? { "Case No": r.case_no, Applicant: r.applicant ?? "", Bank: r.bank ?? "", City: r.city ?? "", "Bank Payout": Number(r.bank_payout_amount), "Bank Received": Number(r.bank_paid_amount), "Bank Balance": Number(r.bank_balance), "Bank Status": r.bank_payment_status, "Bank Paid Date": r.bank_paid_date ?? "", "Bank Reference": r.bank_payment_reference ?? "", Remarks: r.remarks ?? "" } : { "Case No": r.case_no, Applicant: r.applicant ?? "", Executive: r.executive ?? "", City: r.city ?? "", "Executive Payout": Number(r.executive_payout_amount), "Executive Paid": Number(r.executive_paid_amount), "Executive Balance": Number(r.executive_balance), "Executive Status": r.executive_payment_status, "Executive Paid Date": r.executive_paid_date ?? "", "Executive Reference": r.executive_payment_reference ?? "", Remarks: r.remarks ?? "" });
    const sheet = XLSX.utils.json_to_sheet(rows); sheet["!cols"] = Object.keys(rows[0]).map((header) => ({ wch: Math.max(14, header.length + 2) })); const workbook = XLSX.utils.book_new(); const sheetName = kind === "all" ? "All Billing" : kind === "bank" ? "Bank Payout" : "Executive Payout"; XLSX.utils.book_append_sheet(workbook, sheet, sheetName); const filename = kind === "all" ? `jangid-billing-all-${today()}.xlsx` : kind === "bank" ? `jangid-bank-payout-${today()}.xlsx` : `jangid-executive-payout-${today()}.xlsx`; XLSX.writeFile(workbook, filename, { compression: true });
  }

  const inputClass = "rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900";
  return <DashboardLayout>
<section className="space-y-6">
<div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
<div>
<p className="text-sm font-semibold uppercase tracking-[.2em] text-orange-600">Finance</p>
<h1 className="mt-2 text-3xl font-bold dark:text-white">Billing</h1>
</div>
<div className="flex gap-2">
<button onClick={() => setBulkOpen(true)} className="rounded-xl bg-green-600 px-4 py-2.5 font-semibold text-white">Bulk Generate Billing</button>
<button onClick={() => { setEditing(null); setModalOpen(true); }} className="flex items-center gap-2 rounded-xl bg-orange-600 px-4 py-2.5 text-white">
<Plus size={18} />Add Billing</button>
</div>
</div>
<form onSubmit={(event) => { event.preventDefault(); void load(filters); }} className="grid gap-3 rounded-2xl border bg-white p-4 sm:grid-cols-2 lg:grid-cols-4 dark:border-slate-800 dark:bg-slate-900">
<input placeholder="Case No" className={inputClass} value={filters.case_no ?? ""} onChange={(e) => setFilter("case_no", e.target.value)} />{(["bank", "executive", "city"] as const).map((key) => <select key={key} className={inputClass} value={filters[key] ?? ""} onChange={(e) => setFilter(key, e.target.value)}>
<option value="">All {key === "city" ? "Cities" : `${key[0].toUpperCase()}${key.slice(1)}s`}</option>{options[key === "city" ? "cities" : key === "bank" ? "banks" : "executives"].map((value) => <option key={value}>{value}</option>)}</select>)}<select className={inputClass} value={filters.bank_payment_status ?? ""} onChange={(e) => setFilter("bank_payment_status", e.target.value)}>
<option value="">All Bank Statuses</option>{paymentStatuses.map((s) => <option key={s}>{s}</option>)}</select>
<select className={inputClass} value={filters.executive_payment_status ?? ""} onChange={(e) => setFilter("executive_payment_status", e.target.value)}>
<option value="">All Executive Statuses</option>{paymentStatuses.map((s) => <option key={s}>{s}</option>)}</select>
<input type="date" className={inputClass} value={filters.from_date ?? ""} onChange={(e) => setFilter("from_date", e.target.value)} />
<input type="date" className={inputClass} value={filters.to_date ?? ""} onChange={(e) => setFilter("to_date", e.target.value)} />
<button className="rounded-xl bg-slate-900 px-4 py-2 text-white">Apply Filters</button>
<button type="button" onClick={() => { setFilters({}); void load({}); }} className="rounded-xl border px-4 py-2">Clear</button>
</form>
<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value]) => <article key={label} className="rounded-2xl border bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
<p className="text-sm text-slate-500">{label}</p>
<p className="mt-2 text-2xl font-bold dark:text-white">{money(value)}</p>
</article>)}</div>
<div className="flex flex-wrap gap-3">{(["all", "bank", "executive"] as const).map((kind) => <button key={kind} disabled={!records.length} onClick={() => exportSheet(kind)} className="rounded-xl border border-orange-200 bg-orange-50 px-4 py-2 text-sm font-semibold text-orange-700 disabled:opacity-50">Export {kind === "all" ? "All Billing" : kind === "bank" ? "Bank Payout" : "Executive Payout"}</button>)}</div>{error && <p className="rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}<div className="overflow-x-auto rounded-2xl border bg-white dark:border-slate-800 dark:bg-slate-900">{loading ? <p className="p-8 text-center text-slate-500">Loading billing…</p> : !records.length ? <p className="p-8 text-center text-slate-500">No billing records found.</p> : <table className="w-full min-w-[1500px] text-sm">
<thead className="bg-slate-900 text-white">
<tr>{["Case No", "Applicant", "Bank", "Executive", "Bank Payout", "Bank Received", "Bank Balance", "Executive Payout", "Executive Paid", "Executive Balance", "Expected Margin", "Action"].map((h) => <th key={h} className="p-3 text-left">{h}</th>)}</tr>
</thead>
<tbody>{records.map((r) => <tr key={r.id} className="border-b dark:border-slate-800">
<td className="p-3">{r.case_no}</td>
<td className="p-3">{r.applicant || "-"}</td>
<td className="p-3">{r.bank || "-"}</td>
<td className="p-3">{r.executive || "-"}</td>
<td className="p-3">{money(r.bank_payout_amount)}</td>
<td className="p-3">{money(r.bank_paid_amount)}</td>
<td className="p-3">{money(r.bank_balance)}</td>
<td className="p-3">{money(r.executive_payout_amount)}</td>
<td className="p-3">{money(r.executive_paid_amount)}</td>
<td className="p-3">{money(r.executive_balance)}</td>
<td className="p-3 font-semibold">{money(r.expected_gross_margin)}</td>
<td className="p-3">
<button onClick={() => openEdit(r)} aria-label={`Edit billing ${r.case_no}`} className="rounded p-2 text-green-600 hover:bg-green-50">
<Pencil size={17} />
</button>
</td>
</tr>)}</tbody>
</table>}</div>
</section>
<BulkBillingModal open={bulkOpen} cases={cases} onClose={() => setBulkOpen(false)} onCreated={() => load(filters)} />
<BillingModal open={modalOpen} record={editing} cases={availableCases} onClose={() => { setModalOpen(false); setEditing(null); }} onSave={save} />
</DashboardLayout>;
}
