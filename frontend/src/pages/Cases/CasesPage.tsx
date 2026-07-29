import { useEffect, useMemo, useRef, useState } from "react";

import DashboardLayout from "../../layouts/DashboardLayout";
import CaseToolbar from "../../components/cases/CaseToolbar";
import CaseTable from "../../components/cases/CaseTable";
import Pagination from "../../components/cases/Pagination";
import AddCaseModal from "../../components/cases/AddCaseModal";
import EditCaseModal from "../../components/cases/EditCaseModal";
import DeleteCaseDialog from "../../components/cases/DeleteCaseDialog";
import ViewCaseModal from "../../components/cases/ViewCaseModal";

import { getCases } from "../../services/caseService";
import type { Case, CaseStatusFilter } from "../../types/case";

export default function CasesPage() {

  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<CaseStatusFilter>("All");
  const [currentPage, setCurrentPage] = useState(1);
  const [exporting, setExporting] = useState(false);

  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingCase, setEditingCase] = useState<Case | null>(null);
  const [deletingCase, setDeletingCase] = useState<Case | null>(null);
  const [viewingCase, setViewingCase] = useState<Case | null>(null);

  const initializedRef = useRef(false);

  const pageSize = 10;

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    loadCases();
  }, []);

  async function loadCases(options?: { silent?: boolean }) {
    const silent = Boolean(options?.silent);

    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      setError(null);
      const data = await getCases();
      setCases(data);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Unable to load cases. Please try again.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  const filteredCases = useMemo(() => {
    const query = search.trim().toLowerCase();

    return cases.filter((item) => {
      const statusMatch = statusFilter === "All" || item.status === statusFilter;

      if (!statusMatch) {
        return false;
      }

      if (!query) {
        return true;
      }

      const searchableText = [
        item.case_no,
        item.applicant,
        item.mobile,
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(query);
    });
  }, [cases, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredCases.length / pageSize));

  useEffect(() => {
    setCurrentPage(1);
  }, [search, statusFilter]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return filteredCases.slice(start, end);
  }, [filteredCases, currentPage]);

  function handleExport() {
    if (filteredCases.length === 0) {
      return;
    }

    setExporting(true);

    const headers = [
      "Case No",
      "Receive Date",
      "Applicant",
      "Bank",
      "Executive",
      "Status",
      "City",
      "Mobile",
    ];

    const rows = filteredCases.map((item) => [
      item.case_no,
      item.receive_date,
      item.applicant,
      item.bank,
      item.executive,
      item.status,
      item.city,
      item.mobile,
    ]);

    const csv = [headers, ...rows]
      .map((line) => line.map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`).join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cases-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    setExporting(false);
  }

  return (
    <DashboardLayout>

      <CaseToolbar
        search={search}
        statusFilter={statusFilter}
        totalCount={cases.length}
        filteredCount={filteredCases.length}
        refreshing={refreshing}
        exporting={exporting}
        onSearchChange={setSearch}
        onStatusChange={setStatusFilter}
        onRefresh={() => void loadCases({ silent: true })}
        onAddCase={() => setIsAddOpen(true)}
        onExport={handleExport}
      />

      <CaseTable
        cases={paginatedCases}
        loading={loading}
        error={error}
        onView={(item) => setViewingCase(item)}
        onEdit={(item) => setEditingCase(item)}
        onDelete={(item) => setDeletingCase(item)}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={filteredCases.length}
        onPageChange={setCurrentPage}
      />

      <AddCaseModal
        open={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onCreated={() => {
          setIsAddOpen(false);
          void loadCases({ silent: true });
        }}
      />

      <EditCaseModal
        open={Boolean(editingCase)}
        caseItem={editingCase}
        onClose={() => setEditingCase(null)}
        onUpdated={() => {
          setEditingCase(null);
          void loadCases({ silent: true });
        }}
      />

      <DeleteCaseDialog
        open={Boolean(deletingCase)}
        caseItem={deletingCase}
        onClose={() => setDeletingCase(null)}
        onDeleted={() => {
          setDeletingCase(null);
          void loadCases({ silent: true });
        }}
      />

      <ViewCaseModal
        open={Boolean(viewingCase)}
        caseItem={viewingCase}
        onClose={() => setViewingCase(null)}
      />

    </DashboardLayout>
  );
}