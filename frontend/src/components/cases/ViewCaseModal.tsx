import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { getCaseActivity } from "../../services/caseService";
import type { CaseVisitRow, CaseActivity } from "../../types/case";
import StatusBadge from "./StatusBadge";
import CaseVisitsPanel from "./CaseVisitsPanel";

type Props = {
  open: boolean;
  caseItem: CaseVisitRow | null;
  onClose: () => void;
};

type DetailProps = {
  label: string;
  value: string;
};

const ACTIVITY_LABELS: Record<string, string> = {
  CASE_CREATED: "Case Created",
  STATUS_CHANGED: "Status Changed",
  EXECUTIVE_CHANGED: "Executive Changed",
  BANK_CHANGED: "Bank Changed",
  COMPANY_CHANGED: "Company Changed",
  DISTRICT_CHANGED: "District Changed",
  CITY_CHANGED: "City Changed",
  ADDRESS_CHANGED: "Address Changed",
  APPLICANT_CHANGED: "Applicant Changed",
  MOBILE_CHANGED: "Mobile Changed",
  LOS_NUMBER_CHANGED: "LOS Number Changed",
  FOLLOW_UP_CHANGED: "Follow-up Changed",
  FOLLOW_UP_NOTE_CHANGED: "Follow-up Note Changed",
  CLOSED_DATE_CHANGED: "Closed Date Changed",
  FIELD_UPDATED: "Field Updated",
};

function DetailField({ label, value }: DetailProps) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-slate-800 dark:text-slate-200">{value || "-"}</p>
    </div>
  );
}

function activityTitle(activity: CaseActivity): string {
  const label = ACTIVITY_LABELS[activity.activity_type] ?? activity.activity_type;
  if (activity.activity_type !== "FIELD_UPDATED" || !activity.field_name) return label;
  const field = activity.field_name.replaceAll("_", " ");
  return `${label}: ${field.charAt(0).toUpperCase()}${field.slice(1)}`;
}

function activityColor(activity: CaseActivity): string {
  if (activity.activity_type === "CASE_CREATED") return "bg-slate-500";
  if (activity.activity_type === "STATUS_CHANGED") {
    if (activity.new_value === "Positive") return "bg-green-500";
    if (activity.new_value === "Negative") return "bg-red-500";
    return "bg-orange-500";
  }
  return "bg-blue-500";
}

function changeArrowColor(activity: CaseActivity): string {
  if (activity.field_name === "status" && activity.new_value === "Positive") {
    return "text-green-600";
  }
  if (activity.field_name === "status" && activity.new_value === "Negative") {
    return "text-red-600";
  }
  return "text-orange-500";
}

function formatActivityDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export default function ViewCaseModal({ open, caseItem, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<"details" | "visits" | "timeline">("details");
  const [activities, setActivities] = useState<CaseActivity[] | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState<string | null>(null);

  useEffect(() => {
    setActiveTab("details");
    setActivities(null);
    setActivityError(null);
    setActivityLoading(false);
  }, [open, caseItem?.visit_id]);

  async function openTimeline() {
    setActiveTab("timeline");
    if (!caseItem || activities !== null || activityLoading) return;

    setActivityLoading(true);
    setActivityError(null);
    try {
      setActivities(await getCaseActivity(caseItem.case_id));
    } catch (error) {
      setActivityError(error instanceof Error ? error.message : "Unable to load case activity.");
    } finally {
      setActivityLoading(false);
    }
  }

  if (!open || !caseItem) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-5">
      <div className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div>
            <p className="text-sm text-slate-500">Case Details</p>
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white">{caseItem.los_no || "LOS not available"}</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-slate-800" aria-label="Close case details">
            <X size={22} />
          </button>
        </div>

        <div className="flex border-b border-slate-200 px-6 dark:border-slate-800" role="tablist">
          <button type="button" role="tab" aria-selected={activeTab === "details"} onClick={() => setActiveTab("details")} className={`border-b-2 px-4 py-3 text-sm font-semibold ${activeTab === "details" ? "border-orange-500 text-orange-600" : "border-transparent text-slate-500"}`}>Details</button>
          <button type="button" role="tab" aria-selected={activeTab === "visits"} onClick={() => setActiveTab("visits")} className={`border-b-2 px-4 py-3 text-sm font-semibold ${activeTab === "visits" ? "border-orange-500 text-orange-600" : "border-transparent text-slate-500"}`}>Case Visits</button>
          <button type="button" role="tab" aria-selected={activeTab === "timeline"} onClick={() => void openTimeline()} className={`border-b-2 px-4 py-3 text-sm font-semibold ${activeTab === "timeline" ? "border-orange-500 text-orange-600" : "border-transparent text-slate-500"}`}>Timeline</button>
        </div>

        <div className="overflow-y-auto p-6">
          {activeTab === "details" ? (
            <div className="space-y-6">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
                <p className="text-xs uppercase tracking-wide text-slate-500">Status</p>
                <div className="mt-2"><StatusBadge status={caseItem.status} /></div>
              </div>
              <div className="grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-2">
                <DetailField label="LOS / Application No" value={caseItem.los_no} />
                <DetailField label="Visit Type" value={caseItem.visit_type} />
                <DetailField label="Applicant" value={caseItem.applicant} />
                <DetailField label="Receive Date" value={caseItem.receive_date} />
                <DetailField label="Company / Agency" value={caseItem.company} />
                <DetailField label="Bank" value={caseItem.bank} />
                <DetailField label="District" value={caseItem.district} />
                <DetailField label="Loan Type" value={caseItem.loan_type} />
                <DetailField label="Executive" value={caseItem.executive} />
                <DetailField label="Mobile" value={caseItem.mobile} />
                <DetailField label="City" value={caseItem.city} />
                <DetailField label="Landmark" value={caseItem.landmark} />
                <DetailField label="Address" value={caseItem.address} />
                <DetailField label="Negative Reason" value={caseItem.negative_reason} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Remarks</p>
                <p className="mt-1 whitespace-pre-line text-slate-800 dark:text-slate-200">{caseItem.remarks || "-"}</p>
              </div>
              <details className="rounded-lg border border-slate-200 p-4 text-sm text-slate-500">
                <summary className="cursor-pointer font-medium">Technical details</summary>
                <div className="mt-3"><DetailField label="Visit / Case ID" value={`${caseItem.visit_id} / ${caseItem.case_id}`} /></div>
              </details>
            </div>
          ) : activeTab === "visits" ? (
            <CaseVisitsPanel caseItem={caseItem} />
          ) : activityLoading ? (
            <p className="py-10 text-center text-slate-500">Loading activity…</p>
          ) : activityError ? (
            <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{activityError}</p>
          ) : activities?.length ? (
            <ol className="space-y-5">
              {activities.map((activity) => (
                <li key={activity.id} className="relative pl-8">
                  <span className={`absolute left-0 top-1.5 h-3 w-3 rounded-full ${activityColor(activity)}`} />
                  <div className="rounded-xl border border-slate-200 p-4 dark:border-slate-700 dark:bg-slate-800/50">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <h3 className="font-semibold text-slate-900 dark:text-white">{activityTitle(activity)}</h3>
                      <time className="text-xs text-slate-500">{formatActivityDate(activity.performed_at)}</time>
                    </div>
                    {(activity.old_value !== null || activity.new_value !== null) && (
                      <p className="mt-3 break-words text-sm text-slate-700 dark:text-slate-300">
                        <strong className="text-slate-600 dark:text-slate-300">{activity.old_value ?? "-"}</strong>
                        <strong className={`mx-2 ${changeArrowColor(activity)}`}>→</strong>
                        <strong className="text-slate-900 dark:text-white">{activity.new_value ?? "-"}</strong>
                      </p>
                    )}
                    <p className="mt-3 text-xs text-slate-500">By {activity.performed_by_name || "Unknown user"}</p>
                    {activity.remarks && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{activity.remarks}</p>}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="py-10 text-center text-slate-500">No activity recorded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
