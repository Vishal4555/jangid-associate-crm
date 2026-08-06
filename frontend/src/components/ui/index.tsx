import type { FormHTMLAttributes, HTMLAttributes, ReactNode } from "react";

export function PageContainer({ children, className = "" }: HTMLAttributes<HTMLDivElement>) {
  return <main className={`app-page ${className}`}>{children}</main>;
}

export function PageHeader({ eyebrow, title, subtitle, actions }: { eyebrow: string; title: string; subtitle?: string; actions?: ReactNode }) {
  return <header className="ui-page-header">
    <div className="min-w-0">
      <p className="ui-eyebrow">{eyebrow}</p>
      <h1 className="ui-page-title">{title}</h1>
      {subtitle && <p className="ui-page-subtitle">{subtitle}</p>}
    </div>
    {actions && <div className="ui-page-actions">{actions}</div>}
  </header>;
}

export function FilterCard({ children, className = "", ...props }: FormHTMLAttributes<HTMLFormElement>) {
  return <form className={`ui-filter-card ${className}`} {...props}>{children}</form>;
}

export function Card({ children, className = "" }: HTMLAttributes<HTMLElement>) {
  return <section className={`ui-card ${className}`}>{children}</section>;
}

export function DataTable({ children, className = "" }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`ui-table-card ${className}`}><div className="ui-table-scroll">{children}</div></div>;
}

export function Tabs({ children, className = "" }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`ui-tabs ${className}`} role="tablist">{children}</div>;
}

export function Alert({ children, tone = "error", className = "" }: { children: ReactNode; tone?: "error" | "success" | "warning" | "info"; className?: string }) {
  return <div role={tone === "error" ? "alert" : "status"} className={`ui-alert ui-alert-${tone} ${className}`}>{children}</div>;
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="ui-empty-state">{children}</div>;
}

export function ModalShell({ title, subtitle, children, footer, onClose, className = "" }: { title: string; subtitle?: string; children: ReactNode; footer: ReactNode; onClose: () => void; className?: string }) {
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 p-4" role="dialog" aria-modal="true" aria-labelledby="ui-modal-title">
    <section className={`flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-slate-900 ${className}`}>
      <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-slate-800"><div><h2 id="ui-modal-title" className="text-xl font-bold">{title}</h2>{subtitle&&<p className="mt-1 text-sm text-slate-500">{subtitle}</p>}</div><button type="button" onClick={onClose} aria-label="Close dialog" className="rounded-lg border px-3 py-1.5">×</button></header>
      <div className="min-h-0 flex-1 overflow-y-auto p-5">{children}</div>
      <footer className="flex flex-wrap justify-end gap-2 border-t border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-900">{footer}</footer>
    </section>
  </div>;
}
