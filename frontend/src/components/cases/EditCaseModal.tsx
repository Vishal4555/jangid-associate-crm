import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import CaseForm from "./CaseForm";
import {
	caseSchema,
	type CaseFormData,
} from "./caseSchema";
import { updateCase } from "../../services/caseService";
import type { Case } from "../../types/case";

type Props = {
	open: boolean;
	caseItem: Case | null;
	onClose: () => void;
	onUpdated: (updatedCase: Case) => void;
};

const defaultValues: CaseFormData = {
	visit_type: "Residence",
	los_no: "",
	receive_date: "",
	bank: "",
	company_id: undefined,
	company: "",
	district_id: undefined,
	district: "",
	applicant: "",
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

function toFormValues(item: Case): CaseFormData {
	return {
		visit_type: "Residence",
		los_no: item.los_no,
		receive_date: item.receive_date,
		bank: item.bank,
		company_id: item.company_id ?? undefined,
		company: item.company,
		district_id: item.district_id ?? undefined,
		district: item.district,
		applicant: item.applicant,
		loan_type: item.loan_type,
		address: item.address,
		city: item.city,
		mobile: item.mobile,
		executive: item.executive,
		status: item.status,
		negative_reason: item.negative_reason,
		landmark: item.landmark,
		remarks: item.remarks,
	};
}

export default function EditCaseModal({
	open,
	caseItem,
	onClose,
	onUpdated,
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

	useEffect(() => {
		if (open && caseItem) {
			reset(toFormValues(caseItem));
			setSubmitError(null);
		}
	}, [open, caseItem, reset]);

	async function onSubmit(data: CaseFormData) {
		if (!caseItem) return;

		try {
			setSubmitError(null);
			const updated = await updateCase(caseItem.id, data);
			onUpdated(updated);
			onClose();
		} catch (error) {
			setSubmitError(
				error instanceof Error
					? error.message
					: "Unable to update case. Please try again.",
			);
		}
	}

	function handleClose() {
		setSubmitError(null);
		reset(defaultValues);
		onClose();
	}

	if (!open || !caseItem) return null;

	return (
		<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-5">
			<div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
				<div className="flex items-center justify-between border-b px-6 py-4">
					<h2 className="text-2xl font-bold">Edit Case</h2>

					<button
						onClick={handleClose}
						className="hover:bg-gray-100 p-2 rounded-lg"
					>
						<X size={22} />
					</button>
				</div>

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
							className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
						>
							{isSubmitting ? "Saving..." : "Update Case"}
						</button>
					</div>
				</form>
			</div>
		</div>
	);
}
