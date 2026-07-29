import { X } from "lucide-react";

import StatusBadge from "./StatusBadge";
import type { Case } from "../../types/case";

type Props = {
	open: boolean;
	caseItem: Case | null;
	onClose: () => void;
};

type DetailProps = {
	label: string;
	value: string;
};

function DetailField({ label, value }: DetailProps) {
	return (
		<div>
			<p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
			<p className="mt-1 text-slate-800">{value || "-"}</p>
		</div>
	);
}

export default function ViewCaseModal({
	open,
	caseItem,
	onClose,
}: Props) {
	if (!open || !caseItem) return null;

	return (
		<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-5">
			<div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
				<div className="flex items-center justify-between border-b px-6 py-4">
					<div>
						<p className="text-sm text-slate-500">Case Details</p>
						<h2 className="text-2xl font-bold text-slate-800">{caseItem.case_no}</h2>
					</div>

					<button
						onClick={onClose}
						className="hover:bg-gray-100 p-2 rounded-lg"
					>
						<X size={22} />
					</button>
				</div>

				<div className="p-6 space-y-6 overflow-y-auto">
					<div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
						<p className="text-xs uppercase tracking-wide text-slate-500">Status</p>
						<div className="mt-2">
							<StatusBadge status={caseItem.status} />
						</div>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
						<DetailField label="Applicant" value={caseItem.applicant} />
						<DetailField label="Receive Date" value={caseItem.receive_date} />
						<DetailField label="Bank" value={caseItem.bank} />
						<DetailField label="Branch" value={caseItem.branch} />
						<DetailField label="Loan Type" value={caseItem.loan_type} />
						<DetailField label="Product Type" value={caseItem.product_type} />
						<DetailField label="Executive" value={caseItem.executive} />
						<DetailField label="Mobile" value={caseItem.mobile} />
						<DetailField label="City" value={caseItem.city} />
						<DetailField label="Landmark" value={caseItem.landmark} />
						<DetailField label="Address" value={caseItem.address} />
						<DetailField label="Negative Reason" value={caseItem.negative_reason} />
					</div>

					<div>
						<p className="text-xs uppercase tracking-wide text-slate-500">Remarks</p>
						<p className="mt-1 text-slate-800 whitespace-pre-line">{caseItem.remarks || "-"}</p>
					</div>
				</div>
			</div>
		</div>
	);
}
