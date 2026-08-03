import type { CaseStatus } from "../../types/case";

type StatusBadgeProps = {
  status: CaseStatus;
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const styles = {
    Pending: "bg-yellow-100 text-yellow-700",
    Positive: "bg-green-100 text-green-700",
    Negative: "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-sm font-semibold ${styles[status]}`}
    >
      {status}
    </span>
  );
}
