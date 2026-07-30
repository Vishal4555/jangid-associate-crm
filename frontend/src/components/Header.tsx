import { Bell, CalendarDays, ChevronDown, LogOut, Menu, Moon, Sun } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Header({ onMenu }: { onMenu: () => void }) {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);

  const signOut = () => {
    logout();
    navigate("/login");
  };

  const date = new Intl.DateTimeFormat("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="sticky top-0 z-20 flex min-h-[76px] items-center justify-between gap-3 border-b border-slate-200/80 bg-white/90 px-4 shadow-sm shadow-slate-950/[.025] backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/90 dark:shadow-black/20 sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenu}
          aria-label="Open navigation"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 lg:hidden dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          <Menu size={21} aria-hidden="true" />
        </button>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-slate-900 lg:hidden dark:bg-white">
          <img
            src="/branding/ja-logo.png"
            alt="Jangid Associate CRM"
            className="h-8 w-8 object-contain"
          />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-bold tracking-[.08em] text-slate-950 dark:text-white sm:text-lg sm:tracking-tight">
            Jangid Associate CRM
          </p>
          <p className="mt-0.5 hidden text-xs font-medium text-slate-500 sm:block dark:text-slate-400">
            Customer operations workspace
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2.5">
        <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2 text-xs font-medium text-slate-600 md:flex dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
          <CalendarDays size={15} className="text-orange-500" aria-hidden="true" />
          <time>{date}</time>
        </div>
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="grid h-10 w-10 place-items-center rounded-xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          {theme === "dark" ? (
            <Sun size={18} aria-hidden="true" />
          ) : (
            <Moon size={18} aria-hidden="true" />
          )}
        </button>
        <button
          type="button"
          aria-label="Notifications"
          className="relative grid h-10 w-10 place-items-center rounded-xl text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          <Bell size={18} aria-hidden="true" />
          <span
            aria-hidden="true"
            className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-orange-500 ring-2 ring-white dark:ring-slate-950"
          />
        </button>

        <div className="relative">
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            aria-haspopup="menu"
            aria-label="Profile menu"
            className="flex min-h-11 items-center gap-2 rounded-xl p-1.5 transition hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-orange-100 text-xs font-bold text-orange-700 ring-1 ring-orange-200 dark:bg-orange-500/15 dark:text-orange-300 dark:ring-orange-500/20">
              {currentUser?.full_name?.slice(0, 1).toUpperCase() ?? "U"}
            </span>
            <span className="hidden text-left sm:block">
              <span className="block max-w-32 truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {currentUser?.full_name ?? "User"}
              </span>
              <span className="block text-xs font-medium text-slate-500 dark:text-slate-400">
                {currentUser?.role ?? ""}
              </span>
            </span>
            <ChevronDown
              size={15}
              aria-hidden="true"
              className={`hidden text-slate-400 transition-transform sm:block ${open ? "rotate-180" : ""}`}
            />
          </button>

          {open && (
            <div
              role="menu"
              className="absolute right-0 top-[52px] w-48 rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl shadow-slate-950/10 dark:border-slate-700 dark:bg-slate-900 dark:shadow-black/30"
            >
              <div className="border-b border-slate-100 px-3 py-2 sm:hidden dark:border-slate-800">
                <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                  {currentUser?.full_name ?? "User"}
                </p>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                  {currentUser?.role ?? ""}
                </p>
              </div>
              <button
                type="button"
                role="menuitem"
                onClick={signOut}
                className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-950 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:text-white"
              >
                <LogOut size={16} aria-hidden="true" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
