import { Eye, Pencil, Trash2 } from "lucide-react";
import StatusBadge from "./StatusBadge";
import type { CaseVisitRow } from "../../types/case";

interface Props {
  cases: CaseVisitRow[];
  loading: boolean;
  error: string | null;
  onView: (item: CaseVisitRow) => void;
  onEdit: (item: CaseVisitRow) => void;
  onDelete: (item: CaseVisitRow) => void;
  canEdit: boolean;
  canDelete: boolean;
}

function formatTurnaroundTime(receiveDate: string, closedDate: string): string {
  if (!receiveDate || !closedDate) {
    return "—";
  }

  function parseDateOnlyUtc(value: string): number | null {
    const parts = value.split("-");
    if (parts.length !== 3 || parts.some((part) => !/^\d+$/.test(part))) {
      return null;
    }

    const [year, month, day] = parts.map(Number);
    const utc = Date.UTC(year, month - 1, day);
    const parsed = new Date(utc);

    if (
      parts[0].length !== 4 ||
      parts[1].length !== 2 ||
      parts[2].length !== 2 ||
      parsed.getUTCFullYear() !== year ||
      parsed.getUTCMonth() !== month - 1 ||
      parsed.getUTCDate() !== day
    ) {
      return null;
    }

    return utc;
  }

  const receiveUtc = parseDateOnlyUtc(receiveDate);
  const closedUtc = parseDateOnlyUtc(closedDate);
  if (receiveUtc === null || closedUtc === null || closedUtc < receiveUtc) {
    return "—";
  }

  const days = Math.floor((closedUtc - receiveUtc) / 86_400_000);
  return `${days} ${days === 1 ? "day" : "days"}`;
}

function ClampedCell({ value }: { value: string }) {
  return <span className="line-clamp-2 break-words leading-5" title={value || undefined}>{value || "—"}</span>;
}

export default function CaseTable({
  cases,
  loading,
  error,
  onView,
  onEdit,
  onDelete,
  canEdit,
  canDelete,
}: Props) {
  const safeCases = Array.isArray(cases) ? cases : [];

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-10">
        <div className="flex items-center justify-center gap-3 text-slate-600">
          <span className="h-5 w-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
          Loading visits...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (safeCases.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-10 text-center">
        <h3 className="text-lg font-semibold text-slate-700">No visits found</h3>
        <p className="text-slate-500 mt-1">Try changing or clearing the filters.</p>
      </div>
    );
  }

  return (
    <div className="w-full min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">

      <div className="w-full overflow-x-auto">
        <table className="w-full min-w-[1380px] table-auto text-sm">

          <thead className="sticky top-0 z-10 bg-[#0F172A] text-white">

            <tr>
              <th className="p-3 text-left whitespace-nowrap">LOS / Application No</th>
              <th className="p-3 text-left whitespace-nowrap">Visit Type</th>
              <th className="p-3 text-left whitespace-nowrap">Receive Date</th>
              <th className="p-3 text-left whitespace-nowrap">TAT</th>
              <th className="p-3 text-left">Applicant</th>
              <th className="min-w-56 p-3 text-left">Address</th>
              <th className="min-w-44 p-3 text-left">Company</th>
              <th className="min-w-40 p-3 text-left">Bank / Finance Company</th>
              <th className="p-3 text-left">District / City</th>
              <th className="p-3 text-left">Executive</th>
              <th className="p-3 text-left whitespace-nowrap">Status</th>
              <th className="sticky right-0 z-20 bg-[#0F172A] p-3 text-center whitespace-nowrap">Action</th>
            </tr>

          </thead>

          <tbody>

            {safeCases.map((item) => (

              <tr
                key={item.visit_id}
                className="border-b border-slate-100 align-top transition hover:bg-orange-50/50 dark:border-slate-800 dark:hover:bg-slate-800/60"
              >

                <td className="p-3 font-medium text-slate-700 dark:text-slate-200 whitespace-nowrap" title={item.los_no}>{item.los_no || "—"}</td>
                <td className="p-3 whitespace-nowrap">{item.visit_type}</td>

                <td className="p-3 whitespace-nowrap">{item.receive_date || "—"}</td>

                <td className="p-3 whitespace-nowrap">{formatTurnaroundTime(item.receive_date, item.closed_date)}</td>

                <td className="p-3"><ClampedCell value={item.applicant} /></td>

                <td className="p-3"><ClampedCell value={item.address} /></td>

                <td className="p-3"><ClampedCell value={item.company} /></td>

                <td className="p-3"><ClampedCell value={item.bank} /></td>

                <td className="p-3"><ClampedCell value={[item.district, item.city].filter(Boolean).join(" / ")} /></td>

                <td className="p-3"><ClampedCell value={item.executive} /></td>

                <td className="p-3 whitespace-nowrap">
                  <StatusBadge status={item.status} />
                </td>

                <td className="sticky right-0 z-10 bg-white p-3 whitespace-nowrap dark:bg-slate-900">

                  <div className="flex justify-center gap-2">

                    <button
                      onClick={() => onView(item)}
                      className="text-blue-600 hover:bg-blue-50 rounded p-1.5"
                      aria-label={`View case ${item.los_no || "without LOS number"}`}
                      title="View"
                    >
                      <Eye size={18} />
                    </button>

                    {canEdit&&<button
                      onClick={() => onEdit(item)}
                      className="text-green-600 hover:bg-green-50 rounded p-1.5"
                      aria-label={`Edit case ${item.los_no || "without LOS number"}`}
                      title="Edit"
                    >
                      <Pencil size={18} />
                    </button>}

                    {canDelete&&<button
                      onClick={() => onDelete(item)}
                      className="text-red-600 hover:bg-red-50 rounded p-1.5"
                      aria-label={`Delete case ${item.los_no || "without LOS number"}`}
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>}

                  </div>

                </td>

              </tr>

            ))}

          </tbody>

        </table>
      </div>

    </div>
  );
}
