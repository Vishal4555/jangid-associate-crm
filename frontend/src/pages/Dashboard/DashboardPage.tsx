import { useEffect, useRef, useState } from "react";
import {
  Activity,
  BriefcaseBusiness,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  FolderKanban,
  TrendingUp,
  UsersRound,
} from "lucide-react";

import DashboardCard from "../../components/DashboardCard";
import PendingAgeingSection from "../../components/dashboard/PendingAgeingSection";
import DashboardLayout from "../../layouts/DashboardLayout";
import { subscribeCasesChanged } from "../../services/caseChangeEvents";
import { getDashboardSummary, getEmptyDashboardSummary } from "../../services/dashboardService";
import { getTodayFollowUps, getUpcomingFollowUps } from "../../services/followUpService";
import type { Case } from "../../types/case";
import type { DashboardSummary } from "../../types/dashboard";


function formatFollowUp(value: string) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}


export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(getEmptyDashboardSummary);
  const [todayFollowUps, setTodayFollowUps] = useState<Case[]>([]);
  const [upcomingFollowUps, setUpcomingFollowUps] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const initializedRef = useRef(false);

  async function loadDashboard(options?: { silent?: boolean }) {
    if (!options?.silent) {
      setLoading(true);
    }

    try {
      setError(null);
      const [summaryData, todayData, upcomingData] = await Promise.all([
        getDashboardSummary(),
        getTodayFollowUps(),
        getUpcomingFollowUps(),
      ]);
      setSummary(summaryData);
      setTodayFollowUps(todayData);
      setUpcomingFollowUps(upcomingData);
    } catch (loadError) {
      setSummary(getEmptyDashboardSummary());
      setTodayFollowUps([]);
      setUpcomingFollowUps([]);
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load dashboard information.",
      );
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      void loadDashboard();
    }
  }, []);

  useEffect(
    () => subscribeCasesChanged(() => void loadDashboard({ silent: true })),
    [],
  );

  const statusTotal = Math.max(summary.total_cases, 1);
  const bars = [
    summary.pending_cases,
    summary.positive_cases,
    summary.negative_cases,
  ].map((value) => Math.max(8, Math.round((value / statusTotal) * 100)));

  return (
    <DashboardLayout>
      <section className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[.2em] text-orange-600">
            Overview
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Business dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            A clear view of your cases, team activity, and workflow health.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-xl border border-orange-200 bg-orange-50 px-3 py-2 text-sm font-medium text-orange-800 dark:border-orange-900/60 dark:bg-orange-500/10 dark:text-orange-300">
          <Activity size={16} />
          {loading ? "Syncing data…" : "Live case data"}
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className="mb-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <DashboardCard
          title="Total Leads"
          value={summary.total_cases}
          icon={UsersRound}
          tone="blue"
          detail="All cases in the pipeline"
        />
        <DashboardCard
          title="Today's Follow-ups"
          value={todayFollowUps.length}
          icon={Clock3}
          detail="Follow-ups scheduled today"
        />
        <DashboardCard
          title="Pending Cases"
          value={summary.pending_cases}
          icon={FolderKanban}
          tone="slate"
          detail="Require the next action"
        />
        <DashboardCard
          title="Closed Cases"
          value={summary.positive_cases}
          icon={CheckCircle2}
          tone="green"
          detail="Positive outcomes to date"
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_.9fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">Monthly leads</h2>
              <p className="mt-1 text-sm text-slate-500">
                Case intake across the current period
              </p>
            </div>
            <TrendingUp className="text-orange-500" size={22} />
          </div>
          <div className="mt-8 flex h-48 items-end justify-between gap-3" aria-label="Monthly leads chart">
            {[42, 58, 38, 72, 55, 86, Math.max(22, Math.min(98, summary.this_month_cases * 8))].map(
              (height, index) => (
                <div key={index} className="flex flex-1 flex-col items-center gap-2">
                  <div
                    className="w-full rounded-t-lg bg-gradient-to-t from-orange-500 to-orange-300 transition-all"
                    style={{ height: `${height}%` }}
                  />
                  <span className="text-[10px] font-medium text-slate-400">
                    {["M", "T", "W", "T", "F", "S", "S"][index]}
                  </span>
                </div>
              ),
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="font-semibold text-slate-900 dark:text-white">Lead status</h2>
          <p className="mt-1 text-sm text-slate-500">Current case distribution</p>
          <div className="mt-7 space-y-5">
            {[
              ["Pending", summary.pending_cases, bars[0], "bg-orange-500"],
              ["Positive", summary.positive_cases, bars[1], "bg-orange-500"],
              ["Negative", summary.negative_cases, bars[2], "bg-slate-400"],
            ].map(([label, value, width, color]) => (
              <div key={String(label)}>
                <div className="mb-2 flex justify-between text-sm">
                  <span className="font-medium text-slate-700 dark:text-slate-200">
                    {label}
                  </span>
                  <span className="text-slate-500">{value}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800">
                  <div
                    className={`h-2 rounded-full ${color}`}
                    style={{ width: `${width}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-orange-50 text-orange-600 dark:bg-orange-500/10">
              <CircleDollarSign size={20} />
            </span>
            <div>
              <p className="text-sm text-slate-500">Monthly revenue</p>
              <p className="font-semibold text-slate-900 dark:text-white">
                Tracked in reports
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Upcoming follow-ups
          </h2>
          {upcomingFollowUps.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No upcoming follow-ups.</p>
          ) : (
            <ul className="mt-4 max-h-72 space-y-3 overflow-y-auto">
              {upcomingFollowUps.map((item) => (
                <li
                  key={item.id}
                  className="rounded-xl border border-slate-200 p-3 dark:border-slate-700"
                >
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {item.applicant || item.los_no || "LOS not available"}
                  </p>
                  <p className="mt-1 text-xs font-medium text-orange-600 dark:text-orange-400">
                    {formatFollowUp(item.next_follow_up_at)}
                  </p>
                  {item.follow_up_note && (
                    <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                      {item.follow_up_note}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-500/10">
              <BriefcaseBusiness size={20} />
            </span>
            <div>
              <p className="text-sm text-slate-500">This month</p>
              <p className="font-semibold text-slate-900 dark:text-white">
                {summary.this_month_cases.toLocaleString("en-IN")} new cases
              </p>
            </div>
          </div>
        </section>
      </div>
      <PendingAgeingSection />
    </DashboardLayout>
  );
}
