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

export function RoleRoute({
  children,
  allowedRoles,
}: {
  children: ReactNode;
  allowedRoles: Array<"Admin" | "Manager" | "Executive">;
}) {
  const { currentUser, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullScreenLoader label="Checking permissions..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!currentUser || !allowedRoles.includes(currentUser.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}