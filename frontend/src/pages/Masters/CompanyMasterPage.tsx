import { useEffect, useState } from "react";

import DashboardLayout from "../../layouts/DashboardLayout";
import { createMasterRecord, listMasters, updateMasterRecord } from "../../services/masterService";
import type { Company, District } from "../../types/master";
import { useAuth } from "../../context/AuthContext";

type Tab = "companies" | "districts";
const control = "w-full rounded-xl border bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900";

export default function CompanyMasterPage() {
  const {currentUser}=useAuth();
  const [tab, setTab] = useState<Tab>("companies");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [company, setCompany] = useState({name:"",code:"",source_type:"Other" as const,contact_person:"",email:"",mobile:"",is_active:true,remarks:""});
  const [district, setDistrict] = useState({name:"",state:"Rajasthan",is_active:true});
  const canManageCompanies=Boolean(currentUser?.permissions.includes("companies.manage"));
  const canManageDistricts=Boolean(currentUser?.permissions.includes("districts.manage"));
  const canManage=tab==="companies"?canManageCompanies:canManageDistricts;

  const load = async () => {
    try {
      const [companyResponse, districtResponse] = await Promise.all([
        listMasters("companies", {all:true}),
        listMasters("districts", {all:true}),
      ]);
      setCompanies(companyResponse.items);
      setDistricts(districtResponse.items);
      setError("");
    } catch (loadError) {
      setError((loadError as Error).message);
    }
  };

  useEffect(() => { void load(); }, []);

  const add = async (event:React.FormEvent) => {
    event.preventDefault();
    setMessage("");
    try {
      if (tab === "companies") {
        await createMasterRecord("companies", company);
        setCompany({...company,name:"",code:"",contact_person:"",email:"",mobile:"",remarks:""});
        setMessage("Company added");
      } else {
        await createMasterRecord("districts", district);
        setDistrict({...district,name:""});
        setMessage("District added");
      }
      await load();
    } catch (saveError) {
      setError((saveError as Error).message);
    }
  };

  return <DashboardLayout><section className={`space-y-5 ${canManage?"":"[&_th:last-child]:hidden [&_td:last-child]:hidden"}`}>
    <div><p className="text-sm font-semibold uppercase tracking-[.2em] text-orange-600">Masters</p><h1 className="text-3xl font-bold">Companies &amp; Rajasthan Districts</h1></div>
    <div className="flex flex-wrap gap-2">{(["companies","districts"] as Tab[]).map(item=><button key={item} onClick={()=>{setTab(item);setMessage("");setError("")}} className={`rounded-xl px-4 py-2 ${tab===item?"bg-slate-900 text-white":"border"}`}>{item==="companies"?"Companies / Agencies":"Rajasthan Districts"}</button>)}</div>
    {error&&<p role="alert" className="rounded-xl bg-red-50 p-3 text-red-700">{error}</p>}
    {message&&<p role="status" className="rounded-xl bg-green-50 p-3 text-green-700">{message}</p>}
    {canManage&&<form onSubmit={add} className="grid gap-3 rounded-2xl border bg-white p-4 md:grid-cols-3 dark:border-slate-700 dark:bg-slate-900">
      {tab==="companies"?<>
        <input required placeholder="Company name" className={control} value={company.name} onChange={event=>setCompany({...company,name:event.target.value})}/>
        <input placeholder="Code" className={control} value={company.code} onChange={event=>setCompany({...company,code:event.target.value})}/>
        <select className={control} value={company.source_type} onChange={event=>setCompany({...company,source_type:event.target.value as typeof company.source_type})}>{["WhatsApp","Email","Both","Other"].map(item=><option key={item}>{item}</option>)}</select>
        <input placeholder="Contact person" className={control} value={company.contact_person} onChange={event=>setCompany({...company,contact_person:event.target.value})}/>
        <input type="email" placeholder="Email" className={control} value={company.email} onChange={event=>setCompany({...company,email:event.target.value})}/>
        <input placeholder="Mobile" className={control} value={company.mobile} onChange={event=>setCompany({...company,mobile:event.target.value})}/>
        <input placeholder="Remarks" className={control} value={company.remarks} onChange={event=>setCompany({...company,remarks:event.target.value})}/>
      </>:<>
        <input required placeholder="District name" className={control} value={district.name} onChange={event=>setDistrict({...district,name:event.target.value})}/>
        <input readOnly className={control} value="Rajasthan"/>
      </>}
      <button className="rounded-xl bg-orange-600 px-4 py-2 text-white">Add</button>
    </form>}
    <div className="overflow-x-auto rounded-2xl border bg-white dark:border-slate-700 dark:bg-slate-900"><table className="w-full min-w-[760px] text-sm"><thead className="bg-slate-900 text-white"><tr>{(tab==="companies"?["NAME","SOURCE","CONTACT","EMAIL","MOBILE","ACTIVE","ACTION"]:["DISTRICT","STATE","ACTIVE","ACTION"]).map(item=><th key={item} className="p-3 text-left">{item}</th>)}</tr></thead><tbody>
      {tab==="companies"?companies.map(item=><tr key={item.id} className="border-b dark:border-slate-800"><td className="p-3">{item.name}</td><td className="p-3">{item.source_type}</td><td className="p-3">{item.contact_person||"—"}</td><td className="p-3">{item.email||"—"}</td><td className="p-3">{item.mobile||"—"}</td><td className="p-3">{item.is_active?"Active":"Inactive"}</td><td className="p-3"><button onClick={()=>void updateMasterRecord("companies",item.id,{is_active:!item.is_active}).then(load)} className="text-orange-600">{item.is_active?"Deactivate":"Activate"}</button></td></tr>):districts.map(item=><tr key={item.id} className="border-b dark:border-slate-800"><td className="p-3">{item.name}</td><td className="p-3">{item.state}</td><td className="p-3">{item.is_active?"Active":"Inactive"}</td><td className="p-3"><button onClick={()=>void updateMasterRecord("districts",item.id,{is_active:!item.is_active}).then(load)} className="text-orange-600">{item.is_active?"Deactivate":"Activate"}</button></td></tr>)}
    </tbody></table></div>
  </section></DashboardLayout>;
}
