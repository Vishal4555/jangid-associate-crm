import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { PermissionRoute, PublicRoute } from "../components/auth/RouteGuards";
const LoginPage = lazy(() => import("../pages/Login/LoginPage"));
const DashboardPage = lazy(() => import("../pages/Dashboard/DashboardPage"));
const CasesPage = lazy(() => import("../pages/Cases/CasesPage"));
const BillingPage = lazy(() => import("../pages/Billing/BillingPage"));
const RateMastersPage = lazy(() => import("../pages/Billing/RateMastersPage"));
const BillingDashboardPage = lazy(() => import("../pages/Billing/BillingDashboardPage"));
const MastersPage = lazy(() => import("../pages/Masters"));
const CompanyMasterPage = lazy(() => import("../pages/Masters/CompanyMasterPage"));
const SearchPage = lazy(() => import("../pages/Search/SearchPage"));
const ReportsPage = lazy(() => import("../pages/Reports/ReportsPage"));
const UsersPage = lazy(() => import("../pages/Users/UsersPage"));
const SettingsPage = lazy(() => import("../pages/Settings/SettingsPage"));

export default function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-4 rounded-3xl border border-white/10 bg-white/5 px-8 py-7 shadow-2xl backdrop-blur">
          <img
            src="/branding/ja-logo.png"
            alt="Jangid Associate CRM"
            className="h-12 w-12 object-contain"
          />
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-orange-400" />
          <p className="text-sm font-medium text-white/80">Jangid Associate CRM</p>
          <p className="text-xs text-white/60">Loading application...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Suspense fallback={<div className="grid min-h-screen place-items-center bg-slate-50 text-sm font-medium text-slate-600 dark:bg-slate-950 dark:text-slate-300"><div className="flex flex-col items-center gap-3"><img src="/branding/ja-logo.png" alt="Jangid Associate CRM" className="h-12 w-12 object-contain" /><span>Loading Jangid Associate CRM…</span></div></div>}><Routes>
        <Route
          path="/"
          element={
            <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
          }
        />

        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <PermissionRoute permissions={["dashboard.view"]}>
              <DashboardPage />
            </PermissionRoute>
          }
        />

        <Route
          path="/cases"
          element={
            <PermissionRoute permissions={["cases.view"]}>
              <CasesPage />
            </PermissionRoute>
          }
        />

        <Route
          path="/masters"
          element={
            <PermissionRoute permissions={["masters.view"]}>
              <MastersPage />
            </PermissionRoute>
          }
        />

        <Route path="/search" element={<PermissionRoute permissions={["search.view"]}><SearchPage /></PermissionRoute>} />
        <Route path="/masters/companies" element={<PermissionRoute permissions={["masters.view"]}><CompanyMasterPage /></PermissionRoute>} />
        <Route path="/reports" element={<PermissionRoute permissions={["reports.view","reports.view_own"]}><ReportsPage /></PermissionRoute>} />
        <Route path="/billing" element={<PermissionRoute permissions={["billing.view"]}><BillingPage /></PermissionRoute>} />
        <Route path="/billing/payment-register" element={<PermissionRoute permissions={["billing.payment_register"]}><BillingPage /></PermissionRoute>} />
        <Route path="/billing/executive-rates" element={<PermissionRoute permissions={["billing.rate_master"]}><RateMastersPage /></PermissionRoute>} />
        <Route path="/billing/bank-rates" element={<PermissionRoute permissions={["billing.rate_master"]}><RateMastersPage /></PermissionRoute>} />
        <Route path="/billing/dashboard" element={<PermissionRoute permissions={["billing.dashboard"]}><BillingDashboardPage /></PermissionRoute>} />
        <Route path="/billing/rates" element={<Navigate to="/billing/executive-rates" replace />} />
        <Route path="/users" element={<PermissionRoute permissions={["users.view"]}><UsersPage /></PermissionRoute>} />
        <Route path="/settings" element={<PermissionRoute permissions={["settings.view"]}><SettingsPage /></PermissionRoute>} />

        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
        />
      </Routes></Suspense>
    </BrowserRouter>
  );
}
