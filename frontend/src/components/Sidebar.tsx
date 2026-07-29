import {
  LayoutDashboard,
  FolderOpen,
  Search,
  BarChart3,
  Layers3,
  Users,
  Settings,
  LogOut,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { AuthRole } from "../types/auth";

const menus = [
  {
    icon: LayoutDashboard,
    name: "Dashboard",
    path: "/dashboard",
    roles: ["Admin", "Manager", "Executive"],
  },
  {
    icon: FolderOpen,
    name: "Cases",
    path: "/cases",
    roles: ["Admin", "Manager", "Executive"],
  },
  {
    icon: Search,
    name: "Search",
    path: "/search",
    roles: ["Admin", "Manager", "Executive"],
  },
  {
    icon: BarChart3,
    name: "Reports",
    path: "/reports",
    roles: ["Admin", "Manager"],
  },
  {
    icon: Layers3,
    name: "Masters",
    path: "/masters",
    roles: ["Admin", "Manager"],
  },
  {
    icon: Users,
    name: "Users",
    path: "/users",
    roles: ["Admin"],
  },
  {
    icon: Settings,
    name: "Settings",
    path: "/settings",
    roles: ["Admin", "Manager"],
  },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();

  const visibleMenus = menus.filter((item) => {
    const role = currentUser?.role;

    if (!role) {
      return false;
    }

    return item.roles.includes(role as AuthRole);
  });

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-950 text-white">
      <div className="border-b border-white/10 p-6">
        <div className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">
          Jangid
        </div>
        <div className="mt-2 text-2xl font-semibold tracking-tight">
          Associate CRM
        </div>
        <p className="mt-2 text-sm text-white/55">
          Secure workflow access for your team.
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {visibleMenus.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? "bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-400/30"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <item.icon size={18} />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="mb-4 rounded-2xl bg-white/5 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.25em] text-white/45">
            Signed in as
          </p>
          <p className="mt-1 text-sm font-semibold text-white">
            {currentUser?.full_name ?? "User"}
          </p>
          <p className="text-xs text-white/55">{currentUser?.role ?? "-"}</p>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm font-medium text-white transition hover:bg-white/10"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}
