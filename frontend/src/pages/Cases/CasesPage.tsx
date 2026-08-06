import { useEffect, useState } from "react";

import DashboardLayout from "../../layouts/DashboardLayout";
import CaseToolbar from "../../components/cases/CaseToolbar";
import CaseTable from "../../components/cases/CaseTable";
import Pagination from "../../components/cases/Pagination";
import AddCaseModal from "../../components/cases/AddCaseModal";
import EditCaseModal from "../../components/cases/EditCaseModal";
import DeleteCaseDialog from "../../components/cases/DeleteCaseDialog";
import ViewCaseModal from "../../components/cases/ViewCaseModal";

import { getCaseVisitRows } from "../../services/caseService";
import { getMyAssignedCompanies } from "../../services/userService";
import type { CaseVisitRow, CaseStatusFilter, VisitType } from "../../types/case";
import { useAuth } from "../../context/AuthContext";

function exportTat(receiveDate: string, closedDate: string): string {
  if (!receiveDate || !closedDate) return "";

  const toUtc = (value: string): number | null => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
    if (!match) return null;
    const [, yearText, monthText, dayText] = match;
    const year = Number(yearText);
    const month = Number(monthText);
    const day = Number(dayText);
    const utc = Date.UTC(year, month - 1, day);
    const parsed = new Date(utc);
    return parsed.getUTCFullYear() === year &&
      parsed.getUTCMonth() === month - 1 &&
      parsed.getUTCDate() === day
      ? utc
      : null;
  };

  const receiveUtc = toUtc(receiveDate);
  const closedUtc = toUtc(closedDate);
  if (receiveUtc === null || closedUtc === null || closedUtc < receiveUtc) return "";
  return `${Math.floor((closedUtc - receiveUtc) / 86_400_000)} days`;
}

export default function CasesPage() {
  const {currentUser}=useAuth();const has=(code:string)=>Boolean(currentUser?.permissions.includes(code));

  const [cases, setCases] = useState<CaseVisitRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<CaseStatusFilter>("All");
  const [visitType,setVisitType]=useState<"All"|VisitType>("All");
  const [bank,setBank]=useState(""); const [city,setCity]=useState(""); const [executive,setExecutive]=useState("");
  const [companyId,setCompanyId]=useState(""); const [districtId,setDistrictId]=useState("");
  const [dateFrom,setDateFrom]=useState(""); const [dateTo,setDateTo]=useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [noCompanies,setNoCompanies]=useState(false);

  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingCase, setEditingCase] = useState<CaseVisitRow | null>(null);
  const [deletingCase, setDeletingCase] = useState<CaseVisitRow | null>(null);
  const [viewingCase, setViewingCase] = useState<CaseVisitRow | null>(null);

  const pageSize = 20;

  useEffect(() => { const timer = window.setTimeout(() => void loadCases(), 250); return () => window.clearTimeout(timer); }, [search, statusFilter, visitType, bank, city, executive, companyId, districtId, dateFrom, dateTo, currentPage]);
  useEffect(()=>{void getMyAssignedCompanies().then(x=>setNoCompanies(!x.all_companies&&x.companies.length===0)).catch(()=>undefined)},[]);

  async function loadCases(options?: { silent?: boolean }) {
    const silent = Boolean(options?.silent);

    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      setError(null);
      const data = await getCaseVisitRows({ search: search.trim() || undefined,
        status: statusFilter === "All" ? undefined : statusFilter, visit_type: visitType === "All" ? undefined : visitType,
        bank: bank.trim() || undefined, city: city.trim() || undefined, executive: executive.trim() || undefined,
        company_id: companyId ? Number(companyId) : undefined, district_id: districtId ? Number(districtId) : undefined,
        date_from: dateFrom || undefined, date_to: dateTo || undefined, page: currentPage, page_size: pageSize });
      setCases(Array.isArray(data.items) ? data.items : []);
      setTotal(data.total);
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

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  useEffect(() => {
    setCurrentPage(1);
  }, [search, statusFilter, visitType, bank, city, executive, companyId, districtId, dateFrom, dateTo]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  function handleExport() {
    if (cases.length === 0) {
      return;
    }

    setExporting(true);

    const headers = [
      "LOS / Application No",
      "Visit Type",
      "Receive Date",
      "Closed Date",
      "TAT",
      "Applicant",
      "Company",
      "Bank",
      "District",
      "Executive",
      "Status",
      "City",
      "Mobile",
      "Remarks",
    ];

    const rows = cases.map((item) => [
      item.los_no || "",
      item.visit_type,
      item.receive_date,
      item.closed_date,
      exportTat(item.receive_date, item.closed_date),
      item.applicant,
      item.company,
      item.bank,
      item.district,
      item.executive,
      item.status,
      item.city,
      item.mobile,
      item.remarks,
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

      {noCompanies&&<p className="mb-4 rounded-xl bg-amber-50 p-4 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">No companies assigned. Contact Admin.</p>}

      <CaseToolbar
        search={search}
        statusFilter={statusFilter}
        visitType={visitType} bank={bank} city={city} executive={executive} companyId={companyId} districtId={districtId} dateFrom={dateFrom} dateTo={dateTo}
        totalCount={total}
        filteredCount={total}
        refreshing={refreshing}
        exporting={exporting}
        onSearchChange={setSearch}
        onStatusChange={setStatusFilter}
        onFilterChange={(name,value)=>({visitType:setVisitType,bank:setBank,city:setCity,executive:setExecutive,companyId:setCompanyId,districtId:setDistrictId,dateFrom:setDateFrom,dateTo:setDateTo}[name] as ((value:any)=>void))(value)}
        onRefresh={() => void loadCases({ silent: true })}
        onAddCase={() => setIsAddOpen(true)}
        onExport={handleExport}
        canAdd={has("cases.create")&&!noCompanies}
      />

      <CaseTable
        cases={cases}
        loading={loading}
        error={error}
        onView={(item) => setViewingCase(item)}
        onEdit={(item) => setEditingCase(item)}
        onDelete={(item) => setDeletingCase(item)}
        canEdit={has("cases.edit")}
        canDelete={currentUser?.role === "Admin" && has("cases.delete")}
      />

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={total}
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
