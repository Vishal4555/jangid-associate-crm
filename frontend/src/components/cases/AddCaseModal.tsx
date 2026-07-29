import { X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import CaseForm from "./CaseForm";
import {
  caseSchema,
  type CaseFormData,
} from "./caseSchema";
import { createCase } from "../../services/caseService";
import type { Case } from "../../types/case";

type Props = {
  open: boolean;
  onClose: () => void;
  onCreated: (createdCase: Case) => void;
};

const defaultValues: CaseFormData = {
  case_no: "",
  receive_date: "",
  bank: "",
  branch: "",
  applicant: "",
  product_type: "",
  loan_type: "",
  address: "",
  city: "",
  mobile: "",
  executive: "",
  status: "Pending",
  negative_reason: "",
  landmark: "",
  remarks: "",
};

export default function AddCaseModal({
  open,
  onClose,
  onCreated,
}: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    watch,
    setValue,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CaseFormData>({
    resolver: zodResolver(caseSchema),
    defaultValues,
  });

  async function onSubmit(data: CaseFormData) {
    try {
      setSubmitError(null);
      const created = await createCase(data);
      onCreated(created);
      reset(defaultValues);
      onClose();
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : "Unable to create case. Please try again.",
      );
    }
  }

  function handleClose() {
    setSubmitError(null);
    reset(defaultValues);
    onClose();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-5">

      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">

        {/* Header */}

        <div className="flex items-center justify-between border-b px-6 py-4">

          <h2 className="text-2xl font-bold">
            Add New Case
          </h2>

          <button
            onClick={handleClose}
            className="hover:bg-gray-100 p-2 rounded-lg"
          >
            <X size={22} />
          </button>

        </div>

        {/* Form */}

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex-1 flex flex-col min-h-0"
        >

          <div className="flex-1 overflow-y-auto p-6 space-y-6">

            <CaseForm
              register={register}
              errors={errors}
              watch={watch}
              setValue={setValue}
            />

            {submitError && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {submitError}
              </p>
            )}

          </div>

          {/* Footer */}

          <div className="flex justify-end gap-3 p-4 border-t bg-white">

            <button
              type="button"
              onClick={handleClose}
              className="px-5 py-2 rounded-lg border border-gray-300 hover:bg-gray-100"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
            >
              {isSubmitting ? "Saving..." : "Save Case"}
            </button>

          </div>

        </form>

      </div>

    </div>
  );
}