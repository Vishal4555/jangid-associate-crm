import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { updateCaseVisit } from "../../services/caseService";
import type { CaseStatus, CaseVisitRow, VisitType } from "../../types/case";

type Props = { open: boolean; caseItem: CaseVisitRow | null; onClose: () => void; onUpdated: () => void };
type Form = Pick<CaseVisitRow, "visit_type" | "receive_date" | "address" | "district_id" | "city" | "landmark" | "executive" | "status" | "negative_reason" | "remarks">;

export default function EditCaseModal({ open, caseItem, onClose, onUpdated }: Props) {
  const [form, setForm] = useState<Form | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (open && caseItem) setForm({ visit_type: caseItem.visit_type, receive_date: caseItem.receive_date,
      address: caseItem.address, district_id: caseItem.district_id, city: caseItem.city,
      landmark: caseItem.landmark, executive: caseItem.executive, status: caseItem.status,
      negative_reason: caseItem.negative_reason, remarks: caseItem.remarks });
    setError(null);
  }, [open, caseItem]);
  if (!open || !caseItem || !form) return null;
  const set = <K extends keyof Form>(key: K, value: Form[K]) => setForm(current => current ? { ...current, [key]: value } : current);
  async function save() {
    if (!caseItem || !form) return;
    try { setSaving(true); setError(null); await updateCaseVisit(caseItem.case_id, caseItem.visit_id, form); onUpdated(); onClose(); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to update visit."); }
    finally { setSaving(false); }
  }
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-5">
    <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white shadow-2xl dark:bg-slate-900">
      <div className="flex items-center justify-between border-b p-5"><div><p className="text-sm text-slate-500">{caseItem.los_no}</p><h2 className="text-2xl font-bold">Edit {caseItem.visit_type} Visit</h2></div><button onClick={onClose} aria-label="Close"><X /></button></div>
      <div className="grid gap-4 p-6 md:grid-cols-2">
        <label>Visit Type<select value={form.visit_type} onChange={e=>set("visit_type",e.target.value as VisitType)} className="block w-full rounded border p-2">{["Residence","Office","Permanent","Business","Other"].map(x=><option key={x}>{x}</option>)}</select></label>
        <label>Status<select value={form.status} onChange={e=>set("status",e.target.value as CaseStatus)} className="block w-full rounded border p-2">{["Pending","Positive","Negative"].map(x=><option key={x}>{x}</option>)}</select></label>
        <label>Receive Date<input type="date" value={form.receive_date} onChange={e=>set("receive_date",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label>Executive<input value={form.executive} onChange={e=>set("executive",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label className="md:col-span-2">Address<textarea value={form.address} onChange={e=>set("address",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label>City<input value={form.city} onChange={e=>set("city",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label>Landmark<input value={form.landmark} onChange={e=>set("landmark",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label className="md:col-span-2">Negative Reason<input value={form.negative_reason} onChange={e=>set("negative_reason",e.target.value)} className="block w-full rounded border p-2" /></label>
        <label className="md:col-span-2">Remarks<textarea value={form.remarks} onChange={e=>set("remarks",e.target.value)} className="block w-full rounded border p-2" /></label>
        {error && <p className="md:col-span-2 rounded bg-red-50 p-3 text-red-700">{error}</p>}
      </div>
      <div className="flex justify-end gap-3 border-t p-4"><button onClick={onClose} className="rounded border px-4 py-2">Cancel</button><button disabled={saving} onClick={()=>void save()} className="rounded bg-orange-600 px-4 py-2 text-white disabled:opacity-50">{saving ? "Saving..." : "Save Visit"}</button></div>
    </div>
  </div>;
}
