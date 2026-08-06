import { useState, type ReactNode } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
export default function DashboardLayout({ children }: { children: ReactNode; fullWidth?: boolean }) {
  const [collapsed, setCollapsed] = useState(false); const [mobileOpen, setMobileOpen] = useState(false);
  return <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950"><Sidebar collapsed={collapsed} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} onToggle={() => setCollapsed((value) => !value)} /><div className="min-w-0 w-full flex-1"><Header onMenu={() => setMobileOpen(true)} /><main className="app-page">{children}</main></div></div>;
}
