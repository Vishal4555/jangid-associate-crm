export type NotificationType =
  | "OVERDUE_FOLLOW_UP"
  | "TODAY_FOLLOW_UP"
  | "OLD_PENDING_CASE";

export type NotificationSeverity = "info" | "warning" | "critical";

export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  case_id: number;
  case_no: string;
  applicant: string | null;
  executive: string | null;
  occurred_at: string | null;
  due_at: string | null;
  severity: NotificationSeverity;
}
