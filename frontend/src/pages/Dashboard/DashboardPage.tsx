import { useEffect, useRef, useState } from "react";

import DashboardLayout from "../../layouts/DashboardLayout";
import DashboardCard from "../../components/DashboardCard";
import {
  getDashboardSummary,
  getEmptyDashboardSummary,
} from "../../services/dashboardService";
import { subscribeCasesChanged } from "../../services/caseChangeEvents";
import type { DashboardSummary } from "../../types/dashboard";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(getEmptyDashboardSummary);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }

    initializedRef.current = true;
    void loadSummary();
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeCasesChanged(() => {
      void loadSummary({ silent: true });
    });

    return unsubscribe;
  }, []);

  async function loadSummary(options?: { silent?: boolean }) {
    const silent = Boolean(options?.silent);

    if (!silent) {
      setLoading(true);
    }

    try {
      setError(null);
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (loadError) {
      setSummary(getEmptyDashboardSummary());
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load dashboard summary.",
      );
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-4">

        <DashboardCard
          title="Total Cases"
          value={summary.total_cases}
        />

        <DashboardCard
          title="Pending"
          value={summary.pending_cases}
        />

        <DashboardCard
          title="Positive"
          value={summary.positive_cases}
        />

        <DashboardCard
          title="Negative"
          value={summary.negative_cases}
        />

      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <DashboardCard title="Today's Cases" value={summary.today_cases} />
        <DashboardCard title="This Month Cases" value={summary.this_month_cases} />
      </div>

      {loading ? (
        <div className="mt-6 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          Loading dashboard analytics...
        </div>
      ) : null}

      {!loading && error ? (
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {error}
        </div>
      ) : null}

      <div className="mt-8 bg-white rounded-xl shadow p-6">
        <h2 className="text-xl font-bold mb-4">
          Recent Cases
        </h2>

        <p className="text-gray-500">
          Recent case table will be shown here...
        </p>
      </div>
    </DashboardLayout>
  );
}