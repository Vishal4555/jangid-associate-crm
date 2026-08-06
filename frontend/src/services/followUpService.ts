import API from "../api/caseApi";
import type { CaseVisitRow } from "../types/case";


async function getFollowUps(path: "today" | "upcoming" | "overdue"): Promise<CaseVisitRow[]> {
  const response = await API.get<CaseVisitRow[]>(`/follow-ups/${path}`);
  return Array.isArray(response.data) ? response.data : [];
}


export const getTodayFollowUps = () => getFollowUps("today");

export const getUpcomingFollowUps = () => getFollowUps("upcoming");

export const getOverdueFollowUps = () => getFollowUps("overdue");
