import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

function FullScreenLoader({ label }: { label: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
      <div className="flex flex-col items-center gap-4 rounded-3xl border border-white/10 bg-white/5 px-8 py-7 shadow-2xl backdrop-blur">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-orange-400" />
        <p className="text-sm text-white/80">{label}</p>
      </div>
    </div>
  );
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullScreenLoader label="Restoring your session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}

export function PublicRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <FullScreenLoader label="Checking authentication..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

export function PermissionRoute({
  children,
  permissions,
}: {
  children: ReactNode;
  permissions: string[];
}) {
  const { currentUser, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullScreenLoader label="Checking permissions..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!currentUser || !permissions.some((code)=>currentUser.permissions.includes(code))) {
    const destinations:[string,string][]=[["dashboard.view","/dashboard"],["cases.view","/cases"],["search.view","/search"],["reports.view","/reports"],["reports.view_own","/reports"],["users.view","/users"],["masters.view","/masters"],["billing.view","/billing"],["settings.view","/settings"]] as [string,string][];
    const destination=destinations.find(([code])=>currentUser?.permissions.includes(code))?.[1];
    if (!destination || destination===location.pathname) return <div className="grid min-h-screen place-items-center bg-slate-950 p-6 text-center text-white"><div><h1 className="text-xl font-semibold">Access denied</h1><p className="mt-2 text-sm text-slate-300">Your account does not have permission to open this page.</p></div></div>;
    return <Navigate to={destination} replace />;
  }

  return <>{children}</>;
}
