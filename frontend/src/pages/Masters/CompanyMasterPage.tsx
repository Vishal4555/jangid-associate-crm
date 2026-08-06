import { useEffect, useState } from "react";

import DashboardLayout from "../../layouts/DashboardLayout";
import { createMasterRecord, listMasters, updateMasterRecord } from "../../services/masterService";
import type { Company, District } from "../../types/master";
import { useAuth } from "../../context/AuthContext";
import { Alert, DataTable, FilterCard, PageHeader, Tabs } from "../../components/ui";

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

  return <DashboardLayout><section className={`space-y-4 ${canManage?"":"[&_th:last-child]:hidden [&_td:last-child]:hidden"}`}>
    <PageHeader eyebrow="Masters" title="Companies &amp; Rajasthan Districts" subtitle="Manage source companies and service districts." />
    <Tabs>{(["companies","districts"] as Tab[]).map(item=><button role="tab" aria-selected={tab===item} key={item} onClick={()=>{setTab(item);setMessage("");setError("")}} className={`rounded-xl border px-4 py-2 ${tab===item?"border-slate-900 bg-slate-900 text-white":"border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900"}`}>{item==="companies"?"Companies / Agencies":"Rajasthan Districts"}</button>)}</Tabs>
    {error&&<Alert>{error}</Alert>}
    {message&&<Alert tone="success">{message}</Alert>}
    {canManage&&<FilterCard onSubmit={add} className="md:grid-cols-3">
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
    </FilterCard>}
    <DataTable><table className="min-w-[760px]"><thead><tr>{(tab==="companies"?["NAME","SOURCE","CONTACT","EMAIL","MOBILE","ACTIVE","ACTION"]:["DISTRICT","STATE","ACTIVE","ACTION"]).map(item=><th key={item} className="text-left">{item}</th>)}</tr></thead><tbody>
      {tab==="companies"?companies.map(item=><tr key={item.id} className="border-b dark:border-slate-800"><td className="p-3">{item.name}</td><td className="p-3">{item.source_type}</td><td className="p-3">{item.contact_person||"—"}</td><td className="p-3">{item.email||"—"}</td><td className="p-3">{item.mobile||"—"}</td><td className="p-3">{item.is_active?"Active":"Inactive"}</td><td className="p-3"><button onClick={()=>void updateMasterRecord("companies",item.id,{is_active:!item.is_active}).then(load)} className="text-orange-600">{item.is_active?"Deactivate":"Activate"}</button></td></tr>):districts.map(item=><tr key={item.id} className="border-b dark:border-slate-800"><td className="p-3">{item.name}</td><td className="p-3">{item.state}</td><td className="p-3">{item.is_active?"Active":"Inactive"}</td><td className="p-3"><button onClick={()=>void updateMasterRecord("districts",item.id,{is_active:!item.is_active}).then(load)} className="text-orange-600">{item.is_active?"Deactivate":"Activate"}</button></td></tr>)}
    </tbody></table></DataTable>
  </section></DashboardLayout>;
}
