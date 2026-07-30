import { useEffect, useMemo, useState } from "react";
import {
  PencilLine,
  Plus,
  RefreshCcw,
  Search,
  ShieldCheck,
  Trash2,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { listMasters, createMasterRecord, updateMasterRecord, deleteMasterRecord } from "../../services/masterService";
import type {
  Bank,
  Branch,
  Executive,
  LoanType,
  MasterKey,
  MasterRecord,
  ProductType,
} from "../../types/master";

type TabConfig = {
  key: MasterKey;
  title: string;
  subtitle: string;
};

type ColumnConfig = {
  header: string;
  render: (record: MasterRecord) => string;
};

type DialogMode = "create" | "edit" | null;
type DialogValues = Record<string, string>;

const tabs: TabConfig[] = [
  { key: "banks", title: "Banks", subtitle: "Bank masters" },
  { key: "branches", title: "Branches", subtitle: "Branch masters" },
  { key: "executives", title: "Executives", subtitle: "Executive masters" },
  { key: "loan-types", title: "Loan Types", subtitle: "Loan master values" },
  { key: "product-types", title: "Product Types", subtitle: "Product master values" },
];

function emptyValues(master: MasterKey): DialogValues {
  switch (master) {
    case "banks":
      return { name: "", code: "" };
    case "branches":
      return { bank_id: "", name: "", code: "" };
    case "executives":
      return { full_name: "", email: "", mobile: "", status: "Active" };
    case "loan-types":
      return { name: "", code: "" };
    case "product-types":
      return { name: "", code: "" };
    default:
      return { name: "", code: "" };
  }
}

function valuesFromRecord(master: MasterKey, record: MasterRecord): DialogValues {
  switch (master) {
    case "banks": {
      const item = record as Bank;
      return { name: item.name, code: item.code ?? "" };
    }
    case "branches": {
      const item = record as Branch;
      return { bank_id: String(item.bank_id), name: item.name, code: item.code ?? "" };
    }
    case "executives": {
      const item = record as Executive;
      return {
        full_name: item.full_name,
        email: item.email ?? "",
        mobile: item.mobile ?? "",
        status: item.status,
      };
    }
    case "loan-types": {
      const item = record as LoanType;
      return { name: item.name, code: item.code ?? "" };
    }
    case "product-types": {
      const item = record as ProductType;
      return { name: item.name, code: item.code ?? "" };
    }
    default:
      return { name: "", code: "" };
  }
}

function columnsFor(master: MasterKey): ColumnConfig[] {
  switch (master) {
    case "banks":
      return [
        { header: "Name", render: (record) => (record as Bank).name },
        { header: "Code", render: (record) => (record as Bank).code ?? "-" },
      ];
    case "branches":
      return [
        { header: "Bank", render: (record) => (record as Branch).bank_name },
        { header: "Branch", render: (record) => (record as Branch).name },
        { header: "Code", render: (record) => (record as Branch).code ?? "-" },
      ];
    case "executives":
      return [
        { header: "Name", render: (record) => (record as Executive).full_name },
        { header: "Email", render: (record) => (record as Executive).email ?? "-" },
        { header: "Mobile", render: (record) => (record as Executive).mobile ?? "-" },
        { header: "Status", render: (record) => (record as Executive).status },
      ];
    case "loan-types":
      return [
        { header: "Name", render: (record) => (record as LoanType).name },
        { header: "Code", render: (record) => (record as LoanType).code ?? "-" },
      ];
    case "product-types":
      return [
        { header: "Name", render: (record) => (record as ProductType).name },
        { header: "Code", render: (record) => (record as ProductType).code ?? "-" },
      ];
    default:
      return [];
  }
}

function masterLabel(master: MasterKey) {
  return tabs.find((item) => item.key === master)?.title ?? "Masters";
}

export default function MastersPage() {
  const { currentUser } = useAuth();
  const [activeMaster, setActiveMaster] = useState<MasterKey>("banks");
  const [records, setRecords] = useState<MasterRecord[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialogMode, setDialogMode] = useState<DialogMode>(null);
  const [editingRecord, setEditingRecord] = useState<MasterRecord | null>(null);
  const [dialogValues, setDialogValues] = useState<DialogValues>(emptyValues("banks"));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<MasterRecord | null>(null);
  const [referenceBanks, setReferenceBanks] = useState<Bank[]>([]);
  const [referenceLoading, setReferenceLoading] = useState(true);

  const isAdmin = currentUser?.role === "Admin";

  useEffect(() => {
    let cancelled = false;

    async function loadReferenceData() {
      setReferenceLoading(true);

      try {
        const [banks] = await Promise.all([
          listMasters("banks", { all: true }),
        ]);

        if (!cancelled) {
          setReferenceBanks(Array.isArray(banks?.items) ? banks.items : []);
        }
      } catch (referenceError) {
        if (!cancelled) {
          setReferenceBanks([]);
        }
      } finally {
        if (!cancelled) {
          setReferenceLoading(false);
        }
      }
    }

    void loadReferenceData();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadActiveMaster(options?: { silent?: boolean }) {
      const silent = Boolean(options?.silent);

      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      try {
        setError(null);

        const response = await listMasters(activeMaster, {
          search: search.trim() || undefined,
          page,
          pageSize,
        });

        if (!cancelled) {
          const items = Array.isArray(response?.items) ? response.items : [];
          setRecords(items as MasterRecord[]);
          setTotalItems(typeof response?.total === "number" ? response.total : items.length);
        }
      } catch (loadError) {
        if (!cancelled) {
          setRecords([]);
          setTotalItems(0);
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load masters. Please try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void loadActiveMaster();

    return () => {
      cancelled = true;
    };
  }, [activeMaster, page, pageSize, search]);

  useEffect(() => {
    setPage(1);
  }, [activeMaster, search]);

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  const paginatedSummary = useMemo(() => {
    if (totalItems === 0) {
      return "No records";
    }

    const start = (page - 1) * pageSize + 1;
    const end = Math.min(page * pageSize, totalItems);
    return `Showing ${start} to ${end} of ${totalItems}`;
  }, [page, pageSize, totalItems]);

  function openCreateDialog() {
    setEditingRecord(null);
    setDialogMode("create");
    setDialogValues(emptyValues(activeMaster));
  }

  function openEditDialog(record: MasterRecord) {
    setEditingRecord(record);
    setDialogMode("edit");
    setDialogValues(valuesFromRecord(activeMaster, record));
  }

  function closeDialog() {
    setDialogMode(null);
    setEditingRecord(null);
    setDialogValues(emptyValues(activeMaster));
    setIsSubmitting(false);
  }

  async function refreshMasters(options?: { silent?: boolean }) {
    const silent = Boolean(options?.silent);

    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      setError(null);
      const response = await listMasters(activeMaster, {
        search: search.trim() || undefined,
        page,
        pageSize,
      });
      const items = Array.isArray(response?.items) ? response.items : [];
      setRecords(items as MasterRecord[]);
      setTotalItems(typeof response?.total === "number" ? response.total : items.length);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load masters. Please try again.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function handleDialogSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isAdmin) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = buildPayload(activeMaster, dialogValues);

      if (dialogMode === "create") {
        await createMasterRecord(activeMaster, payload as never);
      } else if (dialogMode === "edit" && editingRecord) {
        await updateMasterRecord(activeMaster, editingRecord.id, payload as never);
      }

      closeDialog();
      await refreshMasters({ silent: true });
      await reloadReferenceBanks();
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to save record. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!isAdmin || !deleteTarget) {
      return;
    }

    setIsSubmitting(true);

    try {
      await deleteMasterRecord(activeMaster, deleteTarget.id);
      setDeleteTarget(null);
      await refreshMasters({ silent: true });
      await reloadReferenceBanks();
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Unable to delete record. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function reloadReferenceBanks() {
    try {
      const response = await listMasters("banks", { all: true });
      setReferenceBanks(Array.isArray(response?.items) ? response.items : []);
    } catch {
      setReferenceBanks([]);
    }
  }

  const columns = columnsFor(activeMaster);

  if (!currentUser || (currentUser.role !== "Admin" && currentUser.role !== "Manager")) {
    return (
      <DashboardLayout>
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-8 text-amber-950 shadow-sm">
          <div className="flex items-center gap-3 text-lg font-semibold">
            <ShieldCheck size={20} />
            Masters access restricted
          </div>
          <p className="mt-3 text-sm text-amber-900/80">
            Your role does not have permission to view the Masters module.
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Masters</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">Reference Data</h1>
          <p className="mt-2 text-sm text-slate-600">
            Maintain banks, branches, executives, loan types, and product types in one place.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-right shadow-sm">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Access</p>
          <p className="mt-1 text-sm font-semibold text-slate-800">{currentUser.role}</p>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => {
              setActiveMaster(tab.key);
              setSearch("");
              setPage(1);
            }}
            className={`rounded-2xl border px-4 py-3 text-left transition ${
              activeMaster === tab.key
                ? "border-orange-500 bg-orange-500 text-white shadow-lg shadow-orange-500/20"
                : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            }`}
          >
            <div className="text-sm font-semibold">{tab.title}</div>
            <div className={`text-xs ${activeMaster === tab.key ? "text-white/80" : "text-slate-500"}`}>
              {tab.subtitle}
            </div>
          </button>
        ))}
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-slate-200 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{masterLabel(activeMaster)}</h2>
            <p className="mt-1 text-sm text-slate-500">{paginatedSummary}</p>
          </div>

          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative min-w-[280px]">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search masters..."
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm text-slate-800 outline-none transition focus:border-orange-500 focus:bg-white"
              />
            </div>

            <button
              type="button"
              onClick={() => void refreshMasters({ silent: true })}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              <RefreshCcw size={16} className={refreshing ? "animate-spin" : ""} />
              Refresh
            </button>

            {isAdmin && (
              <button
                type="button"
                onClick={openCreateDialog}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-orange-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-700"
              >
                <Plus size={16} />
                Add {masterLabel(activeMaster).replace(/s$/, "")}
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">#</th>
                {columns.map((column) => (
                  <th key={column.header} className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    {column.header}
                  </th>
                ))}
                {isAdmin && (
                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Actions
                  </th>
                )}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={columns.length + (isAdmin ? 2 : 1)} className="px-5 py-12 text-center text-sm text-slate-500">
                    Loading masters...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={columns.length + (isAdmin ? 2 : 1)} className="px-5 py-12 text-center text-sm text-red-600">
                    {error}
                  </td>
                </tr>
              ) : (records?.length ?? 0) === 0 ? (
                <tr>
                  <td colSpan={columns.length + (isAdmin ? 2 : 1)} className="px-5 py-12 text-center text-sm text-slate-500">
                    No records found.
                  </td>
                </tr>
              ) : (
                (records ?? []).map((record, index) => (
                  <tr key={record.id} className="transition hover:bg-slate-50/80">
                    <td className="px-5 py-4 text-sm text-slate-500">{(page - 1) * pageSize + index + 1}</td>
                    {columns.map((column) => (
                      <td key={column.header} className="px-5 py-4 text-sm text-slate-800">
                        {column.render(record)}
                      </td>
                    ))}
                    {isAdmin && (
                      <td className="px-5 py-4 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => openEditDialog(record)}
                            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-orange-300 hover:bg-orange-50 hover:text-orange-700"
                          >
                            <PencilLine size={15} />
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteTarget(record)}
                            className="inline-flex items-center gap-2 rounded-xl border border-red-200 px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50"
                          >
                            <Trash2 size={15} />
                            Delete
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-600 lg:flex-row lg:items-center lg:justify-between">
          <p>
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1}
              className="rounded-xl border border-slate-200 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>

            <button
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page === totalPages}
              className="rounded-xl border border-slate-200 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {dialogMode && (
        <MasterDialog
          master={activeMaster}
          mode={dialogMode}
          values={dialogValues}
          banks={referenceBanks}
          loadingBanks={referenceLoading}
          isSubmitting={isSubmitting}
          onChange={setDialogValues}
          onClose={closeDialog}
          onSubmit={handleDialogSubmit}
        />
      )}

      {deleteTarget && (
        <ConfirmDeleteDialog
          master={activeMaster}
          record={deleteTarget}
          isSubmitting={isSubmitting}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={() => void handleDelete()}
        />
      )}
    </DashboardLayout>
  );
}

function buildPayload(master: MasterKey, values: DialogValues) {
  switch (master) {
    case "banks":
      return {
        name: values.name?.trim() ?? "",
        code: values.code?.trim() || undefined,
      };
    case "branches":
      return {
        bank_id: Number(values.bank_id ?? ""),
        name: values.name?.trim() ?? "",
        code: values.code?.trim() || undefined,
      };
    case "executives":
      return {
        full_name: values.full_name?.trim() ?? "",
        email: values.email?.trim() || undefined,
        mobile: values.mobile?.trim() || undefined,
        status: (values.status as "Active" | "Inactive") ?? "Active",
      };
    case "loan-types":
      return {
        name: values.name?.trim() ?? "",
        code: values.code?.trim() || undefined,
      };
    case "product-types":
      return {
        name: values.name?.trim() ?? "",
        code: values.code?.trim() || undefined,
      };
    default:
      return { name: "" };
  }
}

type DialogProps = {
  master: MasterKey;
  mode: DialogMode;
  values: DialogValues;
  banks: Bank[];
  loadingBanks: boolean;
  isSubmitting: boolean;
  onChange: (values: DialogValues) => void;
  onClose: () => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

function MasterDialog({
  master,
  mode,
  values,
  banks,
  loadingBanks,
  isSubmitting,
  onChange,
  onClose,
  onSubmit,
}: DialogProps) {
  const title = `${mode === "edit" ? "Edit" : "Add"} ${masterLabel(master).replace(/s$/, "")}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-3xl bg-white shadow-2xl">
        <div className="border-b border-slate-200 px-6 py-5">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Masters</p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">{title}</h3>
        </div>

        <form onSubmit={onSubmit} className="space-y-5 px-6 py-6">
          {master === "branches" && (
            <label className="block text-sm font-medium text-slate-700">
              Bank
              <select
                value={values.bank_id}
                onChange={(event) => onChange({ ...values, bank_id: event.target.value })}
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                required
              >
                <option value="">Select bank</option>
                {loadingBanks ? (
                  <option value="">Loading banks...</option>
                ) : (
                  banks.map((bank) => (
                    <option key={bank.id} value={bank.id}>
                      {bank.name}
                    </option>
                  ))
                )}
              </select>
            </label>
          )}

          {master === "executives" ? (
            <>
              <label className="block text-sm font-medium text-slate-700">
                Full Name
                <input
                  value={values.full_name}
                  onChange={(event) => onChange({ ...values, full_name: event.target.value })}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                  required
                />
              </label>

              <div className="grid gap-5 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Email
                  <input
                    value={values.email}
                    onChange={(event) => onChange({ ...values, email: event.target.value })}
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                    type="email"
                  />
                </label>

                <label className="block text-sm font-medium text-slate-700">
                  Mobile
                  <input
                    value={values.mobile}
                    onChange={(event) => onChange({ ...values, mobile: event.target.value })}
                    className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                  />
                </label>
              </div>

              <label className="block text-sm font-medium text-slate-700">
                Status
                <select
                  value={values.status}
                  onChange={(event) => onChange({ ...values, status: event.target.value as "Active" | "Inactive" })}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </label>
            </>
          ) : (
            <label className="block text-sm font-medium text-slate-700">
              Name
              <input
                value={values.name}
                onChange={(event) => onChange({ ...values, name: event.target.value })}
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
                required
              />
            </label>
          )}

          <label className="block text-sm font-medium text-slate-700">
            Code
            <input
              value={values.code}
              onChange={(event) => onChange({ ...values, code: event.target.value })}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-orange-500 focus:bg-white"
            />
          </label>

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
            <button
              type="button"
              onClick={onClose}
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-2xl bg-orange-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

type ConfirmDeleteProps = {
  master: MasterKey;
  record: MasterRecord;
  isSubmitting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

function ConfirmDeleteDialog({ master, record, isSubmitting, onCancel, onConfirm }: ConfirmDeleteProps) {
  const label =
    master === "branches"
      ? (record as Branch).name
      : master === "executives"
        ? (record as Executive).full_name
        : (record as Bank | LoanType | ProductType).name;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-3xl bg-white shadow-2xl">
        <div className="border-b border-slate-200 px-6 py-5">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Delete</p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Delete {masterLabel(master).replace(/s$/, "")}</h3>
        </div>

        <div className="space-y-4 px-6 py-6">
          <p className="text-sm text-slate-600">
            This will permanently delete <span className="font-semibold text-slate-900">{label}</span>.
          </p>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={isSubmitting}
              className="rounded-2xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
