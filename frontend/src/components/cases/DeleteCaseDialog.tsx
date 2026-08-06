import { AlertTriangle } from "lucide-react";
import { useState } from "react";

import { deleteCaseVisit } from "../../services/caseService";
import type { CaseVisitRow } from "../../types/case";

type Props = {
	open: boolean;
	caseItem: CaseVisitRow | null;
	onClose: () => void;
	onDeleted: (id: number) => void;
};

export default function DeleteCaseDialog({
	open,
	caseItem,
	onClose,
	onDeleted,
}: Props) {
	const [isDeleting, setIsDeleting] = useState(false);
	const [error, setError] = useState<string | null>(null);

	if (!open || !caseItem) return null;

	const targetCase = caseItem;

	async function handleDelete() {
		try {
			setError(null);
			setIsDeleting(true);
			await deleteCaseVisit(targetCase.case_id, targetCase.visit_id);
			onDeleted(targetCase.visit_id);
			onClose();
		} catch (deleteError) {
			setError(
				deleteError instanceof Error
					? deleteError.message
					: "Unable to delete case. Please try again.",
			);
		} finally {
			setIsDeleting(false);
		}
	}

	function handleClose() {
		if (isDeleting) return;
		setError(null);
		onClose();
	}

	return (
		<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-5">
			<div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6">
				<div className="flex items-center gap-3">
					<div className="h-10 w-10 rounded-full bg-red-100 text-red-700 flex items-center justify-center">
						<AlertTriangle size={20} />
					</div>
					<div>
						<h2 className="text-xl font-bold text-slate-800">Delete Visit</h2>
						<p className="text-sm text-slate-500">This action cannot be undone.</p>
					</div>
				</div>

				<div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-3">
					<p className="text-sm text-slate-600">LOS / Application No</p>
					<p className="font-semibold text-slate-800">{targetCase.los_no || "Not available"}</p>
					<p className="mt-1 text-sm text-slate-600">{targetCase.visit_type}</p>
				</div>

				{error && (
					<p className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
						{error}
					</p>
				)}

				<div className="mt-6 flex justify-end gap-3">
					<button
						onClick={handleClose}
						className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100"
						disabled={isDeleting}
					>
						Cancel
					</button>

					<button
						onClick={handleDelete}
						disabled={isDeleting}
						className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
					>
						{isDeleting ? "Deleting..." : "Delete"}
					</button>
				</div>
			</div>
		</div>
	);
}
