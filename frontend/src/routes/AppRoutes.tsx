import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ProtectedRoute, PublicRoute, RoleRoute } from "../components/auth/RouteGuards";
const LoginPage = lazy(() => import("../pages/Login/LoginPage"));
const DashboardPage = lazy(() => import("../pages/Dashboard/DashboardPage"));
const CasesPage = lazy(() => import("../pages/Cases/CasesPage"));
const BillingPage = lazy(() => import("../pages/Billing/BillingPage"));
const RateMastersPage = lazy(() => import("../pages/Billing/RateMastersPage"));
const BillingDashboardPage = lazy(() => import("../pages/Billing/BillingDashboardPage"));
const MastersPage = lazy(() => import("../pages/Masters"));
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
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/cases"
          element={
            <ProtectedRoute>
              <CasesPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/masters"
          element={
            <RoleRoute allowedRoles={["Admin", "Manager"]}>
              <MastersPage />
            </RoleRoute>
          }
        />

        <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
        <Route path="/reports" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><ReportsPage /></RoleRoute>} />
        <Route path="/billing" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><BillingPage /></RoleRoute>} />
        <Route path="/billing/payment-register" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><BillingPage /></RoleRoute>} />
        <Route path="/billing/executive-rates" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><RateMastersPage /></RoleRoute>} />
        <Route path="/billing/bank-rates" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><RateMastersPage /></RoleRoute>} />
        <Route path="/billing/dashboard" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><BillingDashboardPage /></RoleRoute>} />
        <Route path="/billing/rates" element={<Navigate to="/billing/executive-rates" replace />} />
        <Route path="/users" element={<RoleRoute allowedRoles={["Admin"]}><UsersPage /></RoleRoute>} />
        <Route path="/settings" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><SettingsPage /></RoleRoute>} />

        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
        />
      </Routes></Suspense>
    </BrowserRouter>
  );
}
