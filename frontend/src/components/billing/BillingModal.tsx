import { X } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import type { BillingPayload, BillingRecord, PaymentStatus } from "../../types/billing";
import type { Case } from "../../types/case";

function calculatedStatus(payout: string, paid: string): PaymentStatus {
  const payoutAmount = Number(payout) || 0;
  const paidAmount = Number(paid) || 0;
  if (paidAmount <= 0) return "Pending";
  if (paidAmount < payoutAmount) return "Partially Paid";
  return "Paid";
}

function initialPayload(record: BillingRecord | null, cases: Case[]): BillingPayload {
  return {
    case_id: record?.case_id ?? cases[0]?.id ?? 0,
    bank_payout_amount: record?.bank_payout_amount ?? "0.00",
    bank_paid_amount: record?.bank_paid_amount ?? "0.00",
    bank_payment_status: record?.bank_payment_status ?? "Pending",
    bank_paid_date: record?.bank_paid_date ?? null,
    bank_payment_reference: record?.bank_payment_reference ?? null,
    executive_payout_amount: record?.executive_payout_amount ?? "0.00",
    executive_paid_amount: record?.executive_paid_amount ?? "0.00",
    executive_payment_status: record?.executive_payment_status ?? "Pending",
    executive_paid_date: record?.executive_paid_date ?? null,
    executive_payment_reference: record?.executive_payment_reference ?? null,
    remarks: record?.remarks ?? null,
  };
}

type Props = {
  open: boolean;
  record: BillingRecord | null;
  cases: Case[];
  onClose: () => void;
  onSave: (payload: BillingPayload) => Promise<void>;
};

export default function BillingModal({ open, record, cases, onClose, onSave }: Props) {
  const [values, setValues] = useState<BillingPayload>(() => initialPayload(record, cases));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setValues(initialPayload(record, cases));
      setError(null);
    }
  }, [open, record, cases]);

  if (!open) return null;
  const selectedCase = cases.find((item) => item.id === values.case_id);
  const set = <K extends keyof BillingPayload>(key: K, value: BillingPayload[K]) =>
    setValues((current) => ({ ...current, [key]: value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!values.case_id) return setError("Please select a case.");
    setSaving(true);
    setError(null);
    try {
      await onSave({
        ...values,
        bank_payment_status: values.bank_payment_status === "Cancelled" ? "Cancelled" : calculatedStatus(values.bank_payout_amount, values.bank_paid_amount),
        executive_payment_status: values.executive_payment_status === "Cancelled" ? "Cancelled" : calculatedStatus(values.executive_payout_amount, values.executive_paid_amount),
      });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save billing.");
    } finally {
      setSaving(false);
    }
  }

  const inputClass = "mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700 dark:bg-slate-800";
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">{record ? "Edit Billing" : "Add Billing"}</h2>
          <button onClick={onClose} aria-label="Close billing form"><X /></button>
        </div>
        <form onSubmit={submit} className="overflow-y-auto p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="md:col-span-2">Case
              <select disabled={Boolean(record)} className={inputClass} value={values.case_id} onChange={(event) => set("case_id", Number(event.target.value))}>
                <option value={0}>Select case</option>
                {cases.map((item) => <option key={item.id} value={item.id}>{item.los_no || "LOS not available"}</option>)}
              </select>
            </label>
            <div className="md:col-span-2 grid gap-3 rounded-xl bg-slate-50 p-4 sm:grid-cols-4 dark:bg-slate-800">
              {[["Applicant", selectedCase?.applicant], ["Bank", selectedCase?.bank], ["City", selectedCase?.city], ["Executive", selectedCase?.executive]].map(([label, value]) => <span key={label}><small className="text-slate-500">{label}</small><strong className="block">{value || "-"}</strong></span>)}
            </div>
            {(["bank", "executive"] as const).map((kind) => {
              const title = kind === "bank" ? "Bank" : "Executive";
              const amountKey = `${kind}_payout_amount` as const;
              const paidKey = `${kind}_paid_amount` as const;
              const statusKey = `${kind}_payment_status` as const;
              const dateKey = `${kind}_paid_date` as const;
              const referenceKey = `${kind}_payment_reference` as const;
              const status = values[statusKey] === "Cancelled" ? "Cancelled" : calculatedStatus(values[amountKey], values[paidKey]);
              return <div key={kind} className="space-y-4 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
                <h3 className="font-semibold">{title} Payout</h3>
                <label>Payout Amount<input type="number" min="0" step="0.01" required className={inputClass} value={values[amountKey]} onChange={(event) => set(amountKey, event.target.value)} /></label>
                <label>{title} Paid Amount<input type="number" min="0" step="0.01" required className={inputClass} value={values[paidKey]} onChange={(event) => set(paidKey, event.target.value)} /></label>
                <div><span className="text-sm text-slate-500">Calculated Status</span><strong className="mt-1 block">{status}</strong></div>
                <label className="flex items-center gap-2"><input type="checkbox" checked={values[statusKey] === "Cancelled"} onChange={(event) => set(statusKey, event.target.checked ? "Cancelled" : calculatedStatus(values[amountKey], values[paidKey]))} />Cancelled</label>
                <label>Paid Date<input type="date" className={inputClass} value={values[dateKey] ?? ""} onChange={(event) => set(dateKey, event.target.value || null)} /></label>
                <label>Payment Reference<input className={inputClass} value={values[referenceKey] ?? ""} onChange={(event) => set(referenceKey, event.target.value || null)} /></label>
              </div>;
            })}
            <label className="md:col-span-2">Remarks<textarea rows={4} className={inputClass} value={values.remarks ?? ""} onChange={(event) => set("remarks", event.target.value || null)} /></label>
          </div>
          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          <div className="mt-6 flex justify-end gap-3"><button type="button" onClick={onClose} className="rounded-lg border px-4 py-2">Cancel</button><button disabled={saving} className="rounded-lg bg-orange-600 px-5 py-2 text-white disabled:opacity-50">{saving ? "Saving…" : "Save Billing"}</button></div>
        </form>
      </div>
    </div>
  );
}
