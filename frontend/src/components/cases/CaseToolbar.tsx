import { Download, Plus, RefreshCw, Search, Upload, X } from "lucide-react";
import { Card, PageHeader } from "../ui";
import type { ReactNode } from "react";
import type { Bank, Company, District, Executive } from "../../types/master";
import type { CaseStatusFilter, VisitSort, VisitType } from "../../types/case";

type FilterName = "visitType" | "bank" | "city" | "executive" | "companyId" | "districtId" | "dateFrom" | "dateTo";
type Props = {
  search: string; statusFilter: CaseStatusFilter; visitType: "All" | VisitType;
  bank: string; city: string; executive: string; companyId: string; districtId: string;
  dateFrom: string; dateTo: string; sort: VisitSort; totalCount: number; refreshing: boolean; exporting: boolean;
  companies: Company[]; banks: Bank[]; districts: District[]; executives: Executive[];
  onSearchChange: (value: string) => void; onStatusChange: (value: CaseStatusFilter) => void; onSortChange: (value: VisitSort) => void;
  onFilterChange: (name: FilterName, value: string) => void; onClearFilters: () => void;
  onRefresh: () => void; onAddCase: () => void; onExport: () => void; onDownloadTemplate:()=>void; onImport:()=>void; canAdd: boolean;
};

const fieldClass = "w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-800 transition focus:border-orange-400 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white";
function Field({ label, children, wide = false }: { label: string; children: ReactNode; wide?: boolean }) {
  return <label className={wide ? "lg:col-span-2" : ""}><span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>{children}</label>;
}

export default function CaseToolbar(props: Props) {
  const activeFilters = Boolean(props.search || props.statusFilter !== "All" || props.visitType !== "All" || props.bank || props.city || props.executive || props.companyId || props.districtId || props.dateFrom || props.dateTo || props.sort !== "latest_added");
  return <Card className="mb-4">
    <PageHeader eyebrow="Cases" title="All Visits" subtitle={`${props.totalCount} visits found`} actions={<>
        {props.canAdd && <button onClick={props.onAddCase} className="flex items-center gap-2 rounded-xl bg-orange-500 px-4 py-2.5 text-white shadow-lg shadow-orange-500/20 transition hover:bg-orange-600"><Plus size={18}/>New Case</button>}
        {props.canAdd && <button onClick={props.onDownloadTemplate} className="flex items-center gap-2 rounded-xl border px-4 py-2.5"><Download size={18}/>Download Template</button>}
        {props.canAdd && <button onClick={props.onImport} className="flex items-center gap-2 rounded-xl border px-4 py-2.5"><Upload size={18}/>Import Cases</button>}
        <button onClick={props.onRefresh} disabled={props.refreshing} className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-slate-700 hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"><RefreshCw size={18} className={props.refreshing ? "animate-spin" : ""}/>{props.refreshing ? "Refreshing..." : "Refresh"}</button>
        <button onClick={props.onExport} disabled={props.exporting} className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-slate-700 hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"><Download size={18}/>{props.exporting ? "Exporting..." : "Export"}</button>
      </>} />
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-6">
      <Field label="Search" wide><div className="relative"><Search className="absolute left-3 top-3 text-slate-400" size={18}/><input value={props.search} onChange={e=>props.onSearchChange(e.target.value)} placeholder="LOS, applicant, mobile, address..." className={`${fieldClass} pl-10`}/></div></Field>
      <Field label="Status"><select value={props.statusFilter} onChange={e=>props.onStatusChange(e.target.value as CaseStatusFilter)} className={fieldClass}><option value="All">All statuses</option><option>Pending</option><option>Positive</option><option>Negative</option></select></Field>
      <Field label="Visit Type"><select value={props.visitType} onChange={e=>props.onFilterChange("visitType",e.target.value)} className={fieldClass}><option value="All">All visit types</option>{["Residence","Office","Permanent","Business","Other"].map(x=><option key={x}>{x}</option>)}</select></Field>
      <Field label="Company"><select value={props.companyId} onChange={e=>props.onFilterChange("companyId",e.target.value)} className={fieldClass}><option value="">All companies</option>{props.companies.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></Field>
      <Field label="Bank / Finance Company"><select value={props.bank} onChange={e=>props.onFilterChange("bank",e.target.value)} className={fieldClass}><option value="">All banks</option>{props.banks.map(x=><option key={x.id} value={x.name}>{x.name}</option>)}</select></Field>
    </div>
    <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-6">
      <Field label="District"><select value={props.districtId} onChange={e=>props.onFilterChange("districtId",e.target.value)} className={fieldClass}><option value="">All districts</option>{props.districts.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></Field>
      <Field label="City"><input value={props.city} onChange={e=>props.onFilterChange("city",e.target.value)} placeholder="Enter city" className={fieldClass}/></Field>
      <Field label="Executive"><select value={props.executive} onChange={e=>props.onFilterChange("executive",e.target.value)} className={fieldClass}><option value="">All executives</option>{props.executives.map(x=><option key={x.id} value={x.full_name}>{x.full_name}</option>)}</select></Field>
      <Field label="Receive From"><input type="date" value={props.dateFrom} onChange={e=>props.onFilterChange("dateFrom",e.target.value)} className={fieldClass}/></Field>
      <Field label="Receive To"><input type="date" value={props.dateTo} onChange={e=>props.onFilterChange("dateTo",e.target.value)} className={fieldClass}/></Field>
      <Field label="Sort"><select value={props.sort} onChange={e=>props.onSortChange(e.target.value as VisitSort)} className={fieldClass}><option value="latest_added">Latest Added</option><option value="oldest_added">Oldest Added</option><option value="receive_date_desc">Receive Date Newest</option><option value="receive_date_asc">Receive Date Oldest</option></select></Field>
      <div className="flex items-end"><button onClick={props.onClearFilters} disabled={!activeFilters} className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"><X size={17}/>Clear Filters</button></div>
    </div>
  </Card>;
}
