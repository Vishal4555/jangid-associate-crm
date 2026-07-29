import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ProtectedRoute, PublicRoute, RoleRoute } from "../components/auth/RouteGuards";
import LoginPage from "../pages/Login/LoginPage";
import DashboardPage from "../pages/Dashboard/DashboardPage";
import CasesPage from "../pages/Cases/CasesPage";
import MastersPage from "../pages/Masters";
import SearchPage from "../pages/Search/SearchPage";
import ReportsPage from "../pages/Reports/ReportsPage";
import UsersPage from "../pages/Users/UsersPage";
import SettingsPage from "../pages/Settings/SettingsPage";

export default function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading && !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-4 rounded-3xl border border-white/10 bg-white/5 px-8 py-7 shadow-2xl backdrop-blur">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-emerald-400" />
          <p className="text-sm text-white/80">Loading application...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
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
        <Route path="/users" element={<RoleRoute allowedRoles={["Admin"]}><UsersPage /></RoleRoute>} />
        <Route path="/settings" element={<RoleRoute allowedRoles={["Admin", "Manager"]}><SettingsPage /></RoleRoute>} />

        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}
