import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function Header() {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Dashboard</h2>
        <p className="text-sm text-slate-500">
          Welcome back{currentUser?.full_name ? `, ${currentUser.full_name}` : ""}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="font-semibold text-slate-900">
            {currentUser?.full_name ?? "User"}
          </p>
          <p className="text-sm text-slate-500">{currentUser?.role ?? "-"}</p>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </header>
  );
}