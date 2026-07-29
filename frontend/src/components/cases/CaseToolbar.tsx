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
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6">

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

          <button
            onClick={onAddCase}
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Plus size={18} />
            New Case
          </button>

          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="border border-gray-300 px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-100 disabled:opacity-60"
          >
            <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>

          <button
            onClick={onExport}
            disabled={exporting}
            className="border border-gray-300 px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-100"
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
            placeholder="Search by Case No, Applicant, Mobile"
            className="w-full border rounded-lg pl-10 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />

        </div>

        <select
          value={statusFilter}
          onChange={(event) => onStatusChange(event.target.value as CaseStatusFilter)}
          className="border rounded-lg p-2"
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