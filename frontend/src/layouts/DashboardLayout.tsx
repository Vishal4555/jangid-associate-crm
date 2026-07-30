import { useState, type ReactNode } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
export default function DashboardLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false); const [mobileOpen, setMobileOpen] = useState(false);
  return <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950"><Sidebar collapsed={collapsed} mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} onToggle={() => setCollapsed((value) => !value)} /><div className="min-w-0 flex-1"><Header onMenu={() => setMobileOpen(true)} /><main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">{children}</main></div></div>;
}
