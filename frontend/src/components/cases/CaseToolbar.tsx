import { Plus, RefreshCw, Download, Search } from "lucide-react";
import type { CaseStatusFilter } from "../../types/case";

type Props = {
  search: string;
  statusFilter: CaseStatusFilter;
  totalCount: number;
  filteredCount: number;
  refreshing: boolean;
  exporting: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: CaseStatusFilter) => void;
  onRefresh: () => void;
  onAddCase: () => void;
  onExport: () => void;
  canAdd: boolean;
};

export default function CaseToolbar({
  search,
  statusFilter,
  totalCount,
  filteredCount,
  refreshing,
  exporting,
  onSearchChange,
  onStatusChange,
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
            All Cases
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Showing {filteredCount} of {totalCount} records
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        <div className="relative">

          <Search
            className="absolute left-3 top-3 text-gray-400"
            size={18}
          />

          <input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search by LOS / Application No, Applicant, Mobile"
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

      </div>

    </div>
  );
}
