import API from "../api/caseApi";
import type { NotificationItem } from "../types/notification";


export async function getNotifications(): Promise<NotificationItem[]> {
  try {
    const response = await API.get<NotificationItem[]>("/notifications");
    return Array.isArray(response.data) ? response.data.map(item=>({...item,case_no:item.los_no||"LOS not available"})) : [];
  } catch (error) {
    const message =
      typeof error === "object" &&
      error !== null &&
      "response" in error &&
      typeof error.response === "object" &&
      error.response !== null &&
      "data" in error.response &&
      typeof error.response.data === "object" &&
      error.response.data !== null &&
      "detail" in error.response.data &&
      typeof error.response.data.detail === "string"
        ? error.response.data.detail
        : "Unable to load notifications.";
    throw new Error(message);
  }
}
