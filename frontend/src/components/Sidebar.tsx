import {
  BarChart3,
  ChevronLeft,
  FolderOpen,
  Layers3,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  Users,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { AuthRole } from "../types/auth";

type SidebarPath =
  | "/dashboard"
  | "/cases"
  | "/search"
  | "/reports"
  | "/masters"
  | "/users"
  | "/settings";

type MenuItem = {
  icon: LucideIcon;
  name: string;
  path: SidebarPath;
  roles: AuthRole[];
};

const menus: MenuItem[] = [
  { icon: LayoutDashboard, name: "Dashboard", path: "/dashboard", roles: ["Admin", "Manager", "Executive"] },
  { icon: FolderOpen, name: "Cases", path: "/cases", roles: ["Admin", "Manager", "Executive"] },
  { icon: Search, name: "Search", path: "/search", roles: ["Admin", "Manager", "Executive"] },
  { icon: BarChart3, name: "Reports", path: "/reports", roles: ["Admin", "Manager"] },
  { icon: Layers3, name: "Masters", path: "/masters", roles: ["Admin", "Manager"] },
  { icon: Users, name: "Users", path: "/users", roles: ["Admin"] },
  { icon: Settings, name: "Settings", path: "/settings", roles: ["Admin", "Manager"] },
];

export default function Sidebar({
  collapsed,
  mobileOpen,
  onClose,
  onToggle,
}: {
  collapsed: boolean;
  mobileOpen: boolean;
  onClose: () => void;
  onToggle: () => void;
}) {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const visibleMenus = menus.filter(
    (item) => currentUser?.role && item.roles.includes(currentUser.role),
  );

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-[2px] lg:hidden"
        />
      )}

      <aside
        aria-label="Application sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex min-h-screen self-stretch flex-col border-r border-slate-800 bg-[#0F172A] text-white shadow-2xl shadow-slate-950/20 transition-all duration-300 lg:static lg:shadow-none ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } ${collapsed ? "w-20" : "w-72"}`}
      >
        <div
          className={`flex h-20 shrink-0 items-center border-b border-white/10 ${
            collapsed ? "justify-center px-3" : "gap-3 px-5"
          }`}
        >
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/10 shadow-inner">
            <img
              src="/branding/ja-logo.png"
              alt="Jangid Associate CRM"
              className="h-10 w-10 object-contain"
            />
          </span>

          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-bold tracking-[.16em] text-white">
                Jangid Associate CRM
              </p>
              <p className="mt-1 text-[11px] font-semibold tracking-[.14em] text-orange-300">
                CRM WORKSPACE
              </p>
            </div>
          )}

          <button
            type="button"
            aria-label={
              mobileOpen ? "Close navigation" : collapsed ? "Expand navigation" : "Collapse navigation"
            }
            aria-expanded={!collapsed}
            onClick={mobileOpen ? onClose : onToggle}
            className={`h-8 w-8 place-items-center rounded-lg border border-white/10 bg-slate-900 text-slate-300 transition hover:bg-white/10 hover:text-white ${
              collapsed ? "absolute left-16 top-6 hidden lg:grid" : "ml-auto grid"
            }`}
          >
            {mobileOpen ? (
              <X size={18} className="lg:hidden" aria-hidden="true" />
            ) : (
              <ChevronLeft
                size={18}
                className={`hidden transition-transform lg:block ${collapsed ? "rotate-180" : ""}`}
                aria-hidden="true"
              />
            )}
          </button>
        </div>

        <nav aria-label="Main navigation" className="flex-1 overflow-y-auto px-3 py-5">
          {!collapsed && (
            <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[.24em] text-slate-500">
              Workspace
            </p>
          )}
          <div className="space-y-1.5">
            {visibleMenus.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                onClick={onClose}
                title={collapsed ? item.name : undefined}
                className={({ isActive }) =>
                  `group relative flex min-h-11 items-center rounded-xl text-sm font-medium transition-all ${
                    collapsed ? "justify-center px-3" : "gap-3 px-3.5"
                  } ${
                    isActive
                      ? "bg-orange-500 text-white shadow-lg shadow-orange-950/30"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  }`
                }
              >
                <item.icon size={19} className="shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.name}</span>}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="border-t border-white/10 p-3">
          {!collapsed && (
            <div className="mb-2 rounded-xl border border-white/5 bg-white/5 px-3.5 py-3">
              <p className="truncate text-sm font-semibold text-white">
                {currentUser?.full_name ?? "User"}
              </p>
              <p className="mt-1 text-xs font-medium text-slate-400">{currentUser?.role ?? ""}</p>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className={`flex min-h-11 w-full items-center rounded-xl text-sm font-medium text-slate-300 transition hover:bg-white/10 hover:text-white ${
              collapsed ? "justify-center px-3" : "gap-3 px-3.5"
            }`}
            title={collapsed ? "Sign out" : undefined}
            aria-label={collapsed ? "Sign out" : undefined}
          >
            <LogOut size={19} aria-hidden="true" />
            {!collapsed && "Sign out"}
          </button>
        </div>
      </aside>
    </>
  );
}
