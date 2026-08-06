import { Plus, RefreshCw, Download, Search } from "lucide-react";
import type { CaseStatusFilter, VisitType } from "../../types/case";

type Props = {
  search: string;
  statusFilter: CaseStatusFilter;
  visitType: "All" | VisitType; bank: string; city: string; executive: string;
  companyId: string; districtId: string; dateFrom: string; dateTo: string;
  totalCount: number;
  filteredCount: number;
  refreshing: boolean;
  exporting: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: CaseStatusFilter) => void;
  onFilterChange: (name: string, value: string) => void;
  onRefresh: () => void;
  onAddCase: () => void;
  onExport: () => void;
  canAdd: boolean;
};

export default function CaseToolbar({
  search,
  statusFilter,
  visitType, bank, city, executive, companyId, districtId, dateFrom, dateTo,
  totalCount,
  filteredCount,
  refreshing,
  exporting,
  onSearchChange,
  onStatusChange,
  onFilterChange,
  onRefresh,
  onAddCase,
  onExport,
  canAdd,
}: Props) {
  return (
    <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between mb-5">

        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            All Visits
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Showing {filteredCount} of {totalCount} visits
          </p>
        </div>

        <div className="flex flex-wrap gap-3">

          {canAdd&&<button
            onClick={onAddCase}
            className="flex items-center gap-2 rounded-xl bg-orange-500 px-4 py-2.5 text-white shadow-lg shadow-orange-500/20 transition hover:-translate-y-0.5 hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Plus size={18} />
            New Case
          </button>}

          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>

          <button
            onClick={onExport}
            disabled={exporting}
            className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <Download size={18} />
            {exporting ? "Exporting..." : "Export"}
          </button>

        </div>

      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">

        <div className="relative">

          <Search
            className="absolute left-3 top-3 text-gray-400"
            size={18}
          />

          <input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search LOS, applicant, mobile, address, executive or visit type"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-slate-800 transition focus:border-orange-400 focus:bg-white focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />

        </div>

        <select
          value={statusFilter}
          onChange={(event) => onStatusChange(event.target.value as CaseStatusFilter)}
          className="rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-slate-800 transition focus:border-orange-400 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        >
          <option value="All">All Status</option>
          <option value="Pending">Pending</option>
          <option value="Positive">Positive</option>
          <option value="Negative">Negative</option>
        </select>
        <select value={visitType} onChange={e=>onFilterChange("visitType",e.target.value)} className="rounded-xl border p-2.5"><option>All</option>{["Residence","Office","Permanent","Business","Other"].map(x=><option key={x}>{x}</option>)}</select>
        <input value={bank} onChange={e=>onFilterChange("bank",e.target.value)} placeholder="Bank / Finance Company" className="rounded-xl border p-2.5" />
        <input value={city} onChange={e=>onFilterChange("city",e.target.value)} placeholder="City" className="rounded-xl border p-2.5" />
        <input value={executive} onChange={e=>onFilterChange("executive",e.target.value)} placeholder="Executive" className="rounded-xl border p-2.5" />
        <input type="number" min="1" value={companyId} onChange={e=>onFilterChange("companyId",e.target.value)} placeholder="Company ID" className="rounded-xl border p-2.5" />
        <input type="number" min="1" value={districtId} onChange={e=>onFilterChange("districtId",e.target.value)} placeholder="District ID" className="rounded-xl border p-2.5" />
        <label className="text-xs text-slate-500">Receive from<input type="date" value={dateFrom} onChange={e=>onFilterChange("dateFrom",e.target.value)} className="block w-full rounded-xl border p-2" /></label>
        <label className="text-xs text-slate-500">Receive to<input type="date" value={dateTo} onChange={e=>onFilterChange("dateTo",e.target.value)} className="block w-full rounded-xl border p-2" /></label>

      </div>

    </div>
  );
}
