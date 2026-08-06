import { useEffect, useState } from "react";
import { createCaseVisit, deleteCaseVisit, getCaseVisits, updateCaseVisit } from "../../services/caseService";
import type { CaseVisit, CaseVisitPayload, CaseStatus, VisitType } from "../../types/case";
import StatusBadge from "./StatusBadge";
import { useAuth } from "../../context/AuthContext";

type ParentVisitContext = { case_id: number; district_id: number | null; district: string };
const blank = (item: ParentVisitContext): CaseVisitPayload => ({ visit_type: "Residence", address: "", district_id: item.district_id,
  district: item.district, city: "", landmark: "", executive: "", status: "Pending", negative_reason: "",
  receive_date: new Date().toISOString().slice(0, 10), remarks: "", next_follow_up_at: null, follow_up_note: "" });

export default function CaseVisitsPanel({ caseItem }: { caseItem: ParentVisitContext }) {
  const {currentUser}=useAuth();const has=(code:string)=>Boolean(currentUser?.permissions.includes(code));
  const [visits, setVisits] = useState<CaseVisit[]>([]); const [editing, setEditing] = useState<CaseVisit | null>(null);
  const [form, setForm] = useState<CaseVisitPayload>(blank(caseItem)); const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const load = async () => { try { setVisits(await getCaseVisits(caseItem.case_id)); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load visits"); } };
  useEffect(() => { void load(); }, [caseItem.case_id]);
  const set = (key: keyof CaseVisitPayload, value: string) => setForm(current => ({ ...current, [key]: value }));
  const startAdd = () => { setEditing(null); setForm(blank(caseItem)); setOpen(true); };
  const startEdit = (v: CaseVisit) => { setEditing(v); setForm({ visit_type:v.visit_type,address:v.address,district_id:v.district_id,district:v.district,
    city:v.city,landmark:v.landmark,executive:v.executive,status:v.status,negative_reason:v.negative_reason,receive_date:v.receive_date,
    remarks:v.remarks,next_follow_up_at:v.next_follow_up_at,follow_up_note:v.follow_up_note }); setOpen(true); };
  const save = async () => { try { const operational={status:form.status,negative_reason:form.negative_reason,remarks:form.remarks,next_follow_up_at:form.next_follow_up_at,follow_up_note:form.follow_up_note}; editing ? await updateCaseVisit(caseItem.case_id, editing.id, has("visits.edit")?form:operational) : await createCaseVisit(caseItem.case_id, form); setOpen(false); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to save visit"); } };
  const remove = async (v: CaseVisit) => { if (!confirm(`Delete ${v.visit_type} visit?`)) return; await deleteCaseVisit(caseItem.case_id, v.id); await load(); };
  return <div className="space-y-4">
    <div className="flex items-center justify-between"><h3 className="font-semibold">Case Visits</h3>{has("visits.create")&&<button onClick={startAdd} className="rounded-lg bg-orange-600 px-3 py-2 text-sm text-white">Add Visit</button>}</div>
    {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
    <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead><tr className="border-b text-left">{["Visit Type","Address","District","City","Executive","Status","Receive Date","Closed Date","TAT","Remarks","Action"].map(x=><th key={x} className="p-2">{x}</th>)}</tr></thead>
      <tbody>{visits.map(v=><tr key={v.id} className="border-b"><td className="p-2">{v.visit_type}</td><td className="p-2">{v.address||"-"}</td><td className="p-2">{v.district||"-"}</td><td className="p-2">{v.city||"-"}</td><td className="p-2">{v.executive||"-"}</td><td className="p-2"><StatusBadge status={v.status}/></td><td className="p-2">{v.receive_date||"-"}</td><td className="p-2">{v.closed_date||"-"}</td><td className="p-2">{v.tat_days == null ? "-" : `${v.tat_days} days`}</td><td className="p-2">{v.remarks||"-"}</td><td className="p-2 whitespace-nowrap">{(has("visits.edit")||has("cases.edit_assigned"))&&<button onClick={()=>startEdit(v)} className="mr-2 text-orange-700">Edit</button>}{has("visits.delete")&&<button onClick={()=>void remove(v)} className="text-red-600">Delete</button>}</td></tr>)}</tbody></table></div>
    {open && <div className="rounded-xl border bg-slate-50 p-4 dark:bg-slate-800"><div className="grid gap-3 md:grid-cols-2">
      <label>Visit Type<select disabled={!has("visits.edit")} value={form.visit_type} onChange={e=>set("visit_type",e.target.value as VisitType)} className="block w-full rounded border p-2">{["Residence","Office","Permanent","Business","Other"].map(x=><option key={x}>{x}</option>)}</select></label>
      <label>Status<select value={form.status} onChange={e=>set("status",e.target.value as CaseStatus)} className="block w-full rounded border p-2">{["Pending","Positive","Negative"].map(x=><option key={x}>{x}</option>)}</select></label>
      {(["address","city","landmark","executive","receive_date","remarks","negative_reason","follow_up_note"] as const).map(key=><label key={key} className={key==="address"||key==="remarks"?"md:col-span-2":""}>{key.replaceAll("_"," ")}<input disabled={!has("visits.edit")&&!(["remarks","negative_reason","follow_up_note"] as string[]).includes(key)} type={key==="receive_date"?"date":"text"} value={form[key]??""} onChange={e=>set(key,e.target.value)} className="block w-full rounded border p-2 disabled:bg-slate-100"/></label>)}
    </div><div className="mt-3 flex justify-end gap-2"><button onClick={()=>setOpen(false)} className="rounded border px-3 py-2">Cancel</button><button onClick={()=>void save()} className="rounded bg-orange-600 px-3 py-2 text-white">Save Visit</button></div></div>}
  </div>;
}
