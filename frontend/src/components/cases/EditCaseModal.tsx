import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { updateCaseVisit } from "../../services/caseService";
import { listMasters } from "../../services/masterService";
import type { CaseStatus, CaseVisitRow, VisitType } from "../../types/case";
import type { District, Executive } from "../../types/master";
import { Alert, ModalShell } from "../ui";

type Props = { open: boolean; caseItem: CaseVisitRow | null; onClose: () => void; onUpdated: () => void };
type Form = {
  visit_type: VisitType; receive_date: string; executive_id: string; status: CaseStatus;
  address: string; district_id: string; city: string; landmark: string;
  negative_reason: string; remarks: string;
};

const control = "mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 disabled:bg-slate-100 disabled:text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:disabled:bg-slate-800";
const value = (text: string | null | undefined) => text?.trim() || "Not available";

export default function EditCaseModal({ open, caseItem, onClose, onUpdated }: Props) {
  const { currentUser } = useAuth();
  const [form, setForm] = useState<Form | null>(null);
  const [executives, setExecutives] = useState<Executive[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingMasters, setLoadingMasters] = useState(false);
  const [saving, setSaving] = useState(false);
  const operationalOnly = currentUser?.role === "Executive" && !currentUser.permissions.includes("visits.edit");

  useEffect(() => {
    if (!open || !caseItem) return;
    setForm({
      visit_type: caseItem.visit_type, receive_date: caseItem.receive_date || "",
      executive_id: caseItem.executive_id ? String(caseItem.executive_id) : caseItem.executive ? "legacy" : "",
      status: caseItem.status, address: caseItem.address || "",
      district_id: caseItem.district_id ? String(caseItem.district_id) : "",
      city: caseItem.city || "", landmark: caseItem.landmark || "",
      negative_reason: caseItem.negative_reason || "", remarks: caseItem.remarks || "",
    });
    setError(null); setLoadingMasters(true);
    void Promise.all([
      listMasters("executives", { all: true, activeOnly: true }),
      listMasters("districts", { activeOnly: true }),
    ]).then(([executivePage, districtPage]) => {
      setExecutives(executivePage.items); setDistricts(districtPage.items);
    }).catch(reason => setError(reason instanceof Error ? reason.message : "Unable to load dropdown options."))
      .finally(() => setLoadingMasters(false));
  }, [open, caseItem]);

  const legacyExecutive = useMemo(() => caseItem?.executive && !executives.some(item =>
    item.id === caseItem.executive_id || item.full_name === caseItem.executive) ? caseItem.executive : null,
    [caseItem, executives]);
  if (!open || !caseItem || !form) return null;
  const set = <K extends keyof Form>(key: K, next: Form[K]) => setForm(current => current ? { ...current, [key]: next } : current);

  async function save() {
    if (!form || !caseItem) return;
    if (form.status === "Negative" && !form.negative_reason.trim()) {
      setError("Negative Reason is required when Status is Negative."); return;
    }
    const operationalPayload = {
      status: form.status,
      negative_reason: form.status === "Negative" ? form.negative_reason.trim() : null,
      remarks: form.remarks.trim() || null,
    };
    const fullPayload = {
      visit_type: form.visit_type, receive_date: form.receive_date || null,
      status: form.status, address: form.address.trim() || null,
      district_id: form.district_id ? Number(form.district_id) : null,
      city: form.city.trim() || null, landmark: form.landmark.trim() || null,
      negative_reason: form.status === "Negative" ? form.negative_reason.trim() : null,
      remarks: form.remarks.trim() || null,
      ...(form.executive_id !== "legacy" ? { executive_id: form.executive_id ? Number(form.executive_id) : null } : {}),
    };
    try {
      setSaving(true); setError(null);
      await updateCaseVisit(caseItem.case_id, caseItem.visit_id, operationalOnly ? operationalPayload : fullPayload);
      onUpdated();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update visit.");
    } finally { setSaving(false); }
  }

  const footer = <>
    <button type="button" onClick={onClose} className="rounded-lg border px-4 py-2">Cancel</button>
    <button type="button" disabled={saving || loadingMasters} onClick={() => void save()} className="rounded-lg bg-orange-600 px-4 py-2 text-white disabled:opacity-50">{saving ? "Saving..." : "Save Visit"}</button>
  </>;
  return <ModalShell title={`Edit ${caseItem.visit_type} Visit`} subtitle={`LOS / Application No: ${value(caseItem.los_no)}`} onClose={onClose} footer={footer} className="max-w-[960px]">
    <section aria-label="Application context" className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
      <h3 className="mb-3 font-semibold">Application Details</h3>
      <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
        {[['LOS / Application No', caseItem.los_no], ['Applicant', caseItem.applicant], ['Mobile', caseItem.mobile], ['Company', caseItem.company], ['Bank / Finance Company', caseItem.bank]].map(([label, text]) =>
          <div key={label}><dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt><dd className="mt-1 break-words font-medium">{value(text)}</dd></div>)}
      </dl>
    </section>
    <div className="grid gap-4 md:grid-cols-2">
      <label>Visit Type<select disabled={operationalOnly} value={form.visit_type} onChange={event => set("visit_type", event.target.value as VisitType)} className={control}>{["Residence", "Office", "Permanent", "Business", "Other"].map(item => <option key={item}>{item}</option>)}</select></label>
      <label>Receive Date<input disabled={operationalOnly} type="date" value={form.receive_date} onChange={event => set("receive_date", event.target.value)} className={control}/></label>
      <label>Executive<select disabled={operationalOnly || loadingMasters} value={form.executive_id} onChange={event => set("executive_id", event.target.value)} className={control}><option value="">Unassigned</option>{form.executive_id === "legacy" && <option value="legacy">Current: {caseItem.executive} (inactive/not found)</option>}{caseItem.executive_id && !executives.some(item => item.id === caseItem.executive_id) && <option value={caseItem.executive_id}>Current: {caseItem.executive} (inactive/not found)</option>}{legacyExecutive && form.executive_id !== "legacy" && <option value="legacy">Current: {legacyExecutive} (inactive/not found)</option>}{executives.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select></label>
      <label>Status<select value={form.status} onChange={event => { const status = event.target.value as CaseStatus; setForm(current => current ? { ...current, status, negative_reason: status === "Negative" ? current.negative_reason : "" } : current); }} className={control}>{["Pending", "Positive", "Negative"].map(item => <option key={item}>{item}</option>)}</select></label>
      <label className="md:col-span-2">Address<textarea disabled={operationalOnly} rows={3} value={form.address} onChange={event => set("address", event.target.value)} className={control}/></label>
      <label>District<select disabled={operationalOnly || loadingMasters} value={form.district_id} onChange={event => set("district_id", event.target.value)} className={control}><option value="">No district</option>{caseItem.district_id && !districts.some(item => item.id === caseItem.district_id) && <option value={caseItem.district_id}>Current: {caseItem.district} (inactive/not found)</option>}{districts.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>City<input disabled={operationalOnly} value={form.city} onChange={event => set("city", event.target.value)} className={control}/></label>
      <label>Landmark<input disabled={operationalOnly} value={form.landmark} onChange={event => set("landmark", event.target.value)} className={control}/></label>
      <label>Negative Reason<input required={form.status === "Negative"} disabled={form.status !== "Negative"} value={form.negative_reason} onChange={event => set("negative_reason", event.target.value)} className={control}/></label>
      <label className="md:col-span-2">Remarks<textarea rows={3} value={form.remarks} onChange={event => set("remarks", event.target.value)} className={control}/></label>
      {error && <Alert className="md:col-span-2">{error}</Alert>}
    </div>
  </ModalShell>;
}
