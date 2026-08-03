import { Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { subscribeCasesChanged } from "../services/caseChangeEvents";
import { getNotifications } from "../services/notificationService";
import type { NotificationItem } from "../types/notification";


const TYPE_LABELS = {
  OVERDUE_FOLLOW_UP: "Overdue",
  TODAY_FOLLOW_UP: "Today",
  OLD_PENDING_CASE: "Pending ageing",
};

const SEVERITY_STYLES = {
  info: "border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-500/10",
  warning: "border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-500/10",
  critical: "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-500/10",
};

function formatNotificationDate(item: NotificationItem): string | null {
  const value = item.due_at || item.occurred_at;
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: item.due_at ? "short" : undefined }).format(parsed);
}

export default function NotificationCenter() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initializedRef = useRef(false);

  async function load(silent = false) {
    if (!silent) setLoading(true);
    try {
      setItems(await getNotifications());
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load notifications.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      void load();
    }
  }, []);

  useEffect(() => subscribeCasesChanged(() => void load(true)), []);

  function viewCases() {
    setOpen(false);
    navigate("/cases");
  }

  return (
    <div className="relative">
      <button type="button" onClick={() => setOpen((value) => !value)} aria-label="Notifications" aria-expanded={open} className="relative grid h-10 w-10 place-items-center rounded-xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white">
        <Bell size={18} aria-hidden="true" />
        {items.length > 0 && <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-orange-500 px-1 text-center text-[10px] font-bold leading-5 text-white">{items.length > 99 ? "99+" : items.length}</span>}
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 flex max-h-[70vh] w-[min(92vw,26rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800"><div><h2 className="font-semibold text-slate-900 dark:text-white">Notifications</h2><p className="text-xs text-slate-500">{items.length} actionable item{items.length === 1 ? "" : "s"}</p></div></div>
          <div className="overflow-y-auto p-3">
            {loading ? <p className="py-8 text-center text-sm text-slate-500">Loading notifications…</p> : error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : items.length === 0 ? <p className="py-8 text-center text-sm text-slate-500">No notifications right now.</p> : <ul className="space-y-2">{items.map((item) => { const displayDate = formatNotificationDate(item); return <li key={item.id}><button type="button" onClick={viewCases} className={`w-full rounded-xl border p-3 text-left transition hover:shadow-sm ${SEVERITY_STYLES[item.severity]}`}><div className="flex items-start justify-between gap-2"><span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{TYPE_LABELS[item.type]}</span>{displayDate && <span className="text-xs text-slate-500">{displayDate}</span>}</div><p className="mt-1 font-semibold text-slate-900 dark:text-white">{item.title}</p><p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.message}</p><p className="mt-2 text-xs text-slate-500">{item.applicant || "Unknown applicant"} · {item.case_no}</p></button></li>; })}</ul>}
          </div>
          <button type="button" onClick={viewCases} className="border-t border-slate-200 px-4 py-3 text-sm font-semibold text-orange-600 hover:bg-orange-50 dark:border-slate-800 dark:hover:bg-orange-500/10">View all cases</button>
        </div>
      )}
    </div>
  );
}
