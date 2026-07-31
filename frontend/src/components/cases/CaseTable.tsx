import { Eye, Pencil, Trash2 } from "lucide-react";
import StatusBadge from "./StatusBadge";
import type { Case } from "../../types/case";

interface Props {
  cases: Case[];
  loading: boolean;
  error: string | null;
  onView: (item: Case) => void;
  onEdit: (item: Case) => void;
  onDelete: (item: Case) => void;
}

export default function CaseTable({
  cases,
  loading,
  error,
  onView,
  onEdit,
  onDelete,
}: Props) {
  const safeCases = Array.isArray(cases) ? cases : [];

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-10">
        <div className="flex items-center justify-center gap-3 text-slate-600">
          <span className="h-5 w-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
          Loading cases...
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
        <h3 className="text-lg font-semibold text-slate-700">No cases found</h3>
        <p className="text-slate-500 mt-1">Try changing search or status filters.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1380px]">

          <thead className="sticky top-0 z-10 bg-[#0F172A] text-white">

            <tr>
              <th className="p-3 text-left">Case No</th>
              <th className="p-3 text-left">Receive Date</th>
              <th className="p-3 text-left">Closed Date</th>
              <th className="p-3 text-left">Applicant</th>
              <th className="p-3 text-left">Address</th>
              <th className="p-3 text-left">Bank</th>
              <th className="p-3 text-left">City</th>
              <th className="p-3 text-left">Executive</th>
              <th className="p-3 text-left">Status</th>
              <th className="sticky right-0 bg-[#0F172A] p-3 text-center">Action</th>
            </tr>

          </thead>

          <tbody>

            {safeCases.map((item) => (

              <tr
                key={item.id}
                className="border-b border-slate-100 transition hover:bg-orange-50/50 dark:border-slate-800 dark:hover:bg-slate-800/60"
              >

                <td className="p-3 font-medium text-slate-700">{item.case_no}</td>

                <td className="p-3">{item.receive_date || "-"}</td>

                <td className="p-3">-</td>

                <td className="p-3">{item.applicant || "-"}</td>

                <td className="max-w-72 p-3">
                  <span
                    className="block truncate whitespace-nowrap"
                    title={item.address || undefined}
                  >
                    {item.address || "-"}
                  </span>
                </td>

                <td className="p-3">{item.bank || "-"}</td>

                <td className="p-3">{item.city || "-"}</td>

                <td className="p-3">{item.executive || "-"}</td>

                <td className="p-3">
                  <StatusBadge status={item.status} />
                </td>

                <td className="sticky right-0 bg-white p-3 dark:bg-slate-900">

                  <div className="flex justify-center gap-2">

                    <button
                      onClick={() => onView(item)}
                      className="text-blue-600 hover:bg-blue-50 rounded p-1.5"
                      aria-label={`View case ${item.case_no}`}
                      title="View"
                    >
                      <Eye size={18} />
                    </button>

                    <button
                      onClick={() => onEdit(item)}
                      className="text-green-600 hover:bg-green-50 rounded p-1.5"
                      aria-label={`Edit case ${item.case_no}`}
                      title="Edit"
                    >
                      <Pencil size={18} />
                    </button>

                    <button
                      onClick={() => onDelete(item)}
                      className="text-red-600 hover:bg-red-50 rounded p-1.5"
                      aria-label={`Delete case ${item.case_no}`}
                      title="Delete"
                    >
                      <Trash2 size={18} />
                    </button>

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
