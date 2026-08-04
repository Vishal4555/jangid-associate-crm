import { useEffect, useMemo, useState } from "react";
import type {
  FieldErrors,
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
} from "react-hook-form";

import { listMasters } from "../../services/masterService";
import type { Bank, Branch, Company, CompanyBank, District, Executive, LoanType, ProductType } from "../../types/master";
import type { CaseFormData } from "./caseSchema";

type Props = {
  register: UseFormRegister<CaseFormData>;
  errors: FieldErrors<CaseFormData>;
  watch: UseFormWatch<CaseFormData>;
  setValue: UseFormSetValue<CaseFormData>;
};

export default function CaseForm({ register, errors, watch, setValue }: Props) {
  const [banks, setBanks] = useState<Bank[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyBanks, setCompanyBanks] = useState<CompanyBank[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [executives, setExecutives] = useState<Executive[]>([]);
  const [loanTypes, setLoanTypes] = useState<LoanType[]>([]);
  const [productTypes, setProductTypes] = useState<ProductType[]>([]);
  const [loadingMasters, setLoadingMasters] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const selectedBank = watch("bank");
  const selectedCompanyId = watch("company_id");
  const selectedBranch = watch("branch");

  useEffect(() => {
    let cancelled = false;

    async function loadMasters() {
      setLoadingMasters(true);

      try {
        const [bankResponse, branchResponse, executiveResponse, loanTypeResponse, productTypeResponse, companyResponse, companyBankResponse, districtResponse] =
          await Promise.all([
            listMasters("banks", { all: true }),
            listMasters("branches", { all: true }),
            listMasters("executives", { all: true, activeOnly: true }),
            listMasters("loan-types", { all: true }),
            listMasters("product-types", { all: true }),
            listMasters("companies", { all: true, activeOnly: true }),
            listMasters("company-banks", { all: true, activeOnly: true }),
            listMasters("districts", { all: true, activeOnly: true }),
          ]);

        if (!cancelled) {
          setBanks(Array.isArray(bankResponse?.items) ? bankResponse.items : []);
          setBranches(Array.isArray(branchResponse?.items) ? branchResponse.items : []);
          setExecutives(Array.isArray(executiveResponse?.items) ? executiveResponse.items : []);
          setLoanTypes(Array.isArray(loanTypeResponse?.items) ? loanTypeResponse.items : []);
          setProductTypes(Array.isArray(productTypeResponse?.items) ? productTypeResponse.items : []);
          setCompanies(companyResponse.items);
          setCompanyBanks(companyBankResponse.items);
          setDistricts(districtResponse.items);
          setLoadError(null);
        }
      } catch (masterError) {
        if (!cancelled) {
          setLoadError(
            masterError instanceof Error
              ? masterError.message
              : "Unable to load master data. Please try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingMasters(false);
        }
      }
    }

    void loadMasters();

    return () => {
      cancelled = true;
    };
  }, []);

  const branchOptions = useMemo(() => {
    if (!selectedBank) {
      return branches;
    }

    return branches.filter((branch) => branch.bank_name === selectedBank);
  }, [branches, selectedBank]);

  const bankOptions = useMemo(() => {
    if (!selectedCompanyId) return [];
    const mapped = new Set(companyBanks.filter(item => item.company_id === Number(selectedCompanyId) && item.is_active).map(item => item.bank_id));
    return banks.filter(bank => mapped.has(bank.id));
  }, [banks, companyBanks, selectedCompanyId]);

  useEffect(() => {
    if (selectedBank && !bankOptions.some(bank => bank.name === selectedBank)) {
      setValue("bank", "");
      setValue("branch", "");
    }
  }, [bankOptions, selectedBank, setValue]);

  useEffect(() => {
    if (!selectedBranch) {
      return;
    }

    const branchStillValid = branchOptions.some((branch) => branch.name === selectedBranch);

    if (!branchStillValid) {
      setValue("branch", "");
    }
  }, [branchOptions, selectedBranch, setValue]);

  return (
    <div className="space-y-6">
      {loadError && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {loadError}
        </p>
      )}

      {loadingMasters && (
        <p className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Loading master data...
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium">Case No</label>

          <input {...register("case_no")} className="w-full rounded-lg border px-3 py-2" />

          {errors.case_no && <p className="mt-1 text-sm text-red-500">{errors.case_no.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">LOS / Application No</label>
          <input {...register("los_no")} maxLength={100} className="w-full rounded-lg border px-3 py-2" />
          {errors.los_no && <p className="mt-1 text-sm text-red-500">{errors.los_no.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Receive Date</label>

          <input
            type="date"
            {...register("receive_date")}
            className="w-full rounded-lg border px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Company / Agency</label>
          <select {...register("company_id", { setValueAs: value => value === "" ? undefined : Number(value) })} className="w-full rounded-lg border bg-white px-3 py-2" disabled={loadingMasters}>
            <option value="">Select company</option>
            {companies.map(company => <option key={company.id} value={company.id}>{company.name}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Bank</label>

          <select
            {...register("bank")}
            className="w-full rounded-lg border bg-white px-3 py-2"
            disabled={loadingMasters || !selectedCompanyId}
          >
            <option value="">Select bank</option>
            {bankOptions.map((bank) => (
              <option key={bank.id} value={bank.name}>
                {bank.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Branch</label>

          <select
            {...register("branch")}
            className="w-full rounded-lg border bg-white px-3 py-2"
            disabled={loadingMasters}
          >
            <option value="">Select branch</option>
            {branchOptions.map((branch) => (
              <option key={branch.id} value={branch.name}>
                {branch.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Applicant</label>

          <input {...register("applicant")} className="w-full rounded-lg border px-3 py-2" />

          {errors.applicant && <p className="mt-1 text-sm text-red-500">{errors.applicant.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Mobile</label>

          <input {...register("mobile")} className="w-full rounded-lg border px-3 py-2" />

          {errors.mobile && <p className="mt-1 text-sm text-red-500">{errors.mobile.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Loan Type</label>

          <select
            {...register("loan_type")}
            className="w-full rounded-lg border bg-white px-3 py-2"
            disabled={loadingMasters}
          >
            <option value="">Select loan type</option>
            {loanTypes.map((loanType) => (
              <option key={loanType.id} value={loanType.name}>
                {loanType.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Product Type</label>

          <select
            {...register("product_type")}
            className="w-full rounded-lg border bg-white px-3 py-2"
            disabled={loadingMasters}
          >
            <option value="">Select product type</option>
            {productTypes.map((productType) => (
              <option key={productType.id} value={productType.name}>
                {productType.name}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-medium">Address</label>

          <textarea rows={3} {...register("address")} className="w-full rounded-lg border px-3 py-2" />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">District</label>
          <select {...register("district_id", { setValueAs: value => value === "" ? undefined : Number(value) })} className="w-full rounded-lg border bg-white px-3 py-2" disabled={loadingMasters}>
            <option value="">Select Rajasthan district</option>
            {districts.map(district => <option key={district.id} value={district.id}>{district.name}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">City</label>

          <input {...register("city")} className="w-full rounded-lg border px-3 py-2" />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Landmark</label>

          <input {...register("landmark")} className="w-full rounded-lg border px-3 py-2" />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Executive</label>

          <select
            {...register("executive")}
            className="w-full rounded-lg border bg-white px-3 py-2"
            disabled={loadingMasters}
          >
            <option value="">Select executive</option>
            {executives.map((executive) => (
              <option key={executive.id} value={executive.full_name}>
                {executive.full_name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Status</label>

          <select {...register("status")} className="w-full rounded-lg border px-3 py-2">
            <option value="Pending">Pending</option>
            <option value="Positive">Positive</option>
            <option value="Negative">Negative</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-medium">Negative Reason</label>

          <input {...register("negative_reason")} className="w-full rounded-lg border px-3 py-2" />
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-medium">Remarks</label>

          <textarea rows={4} {...register("remarks")} className="w-full rounded-lg border px-3 py-2" />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Next Follow-up Date &amp; Time</label>

          <input
            type="datetime-local"
            {...register("next_follow_up_at")}
            className="w-full rounded-lg border px-3 py-2"
          />
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-medium">Follow-up Note</label>

          <textarea
            rows={3}
            {...register("follow_up_note")}
            className="w-full rounded-lg border px-3 py-2"
          />
        </div>
      </div>
    </div>
  );
}
