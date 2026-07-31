import API from "../api/caseApi";
import type { Case } from "../types/case";
import { mapCaseResponse, type CaseApiResponse } from "./caseService";


async function getFollowUps(path: "today" | "upcoming" | "overdue"): Promise<Case[]> {
  const response = await API.get<CaseApiResponse[]>(`/follow-ups/${path}`);
  return Array.isArray(response.data) ? response.data.map(mapCaseResponse) : [];
}


export const getTodayFollowUps = () => getFollowUps("today");

export const getUpcomingFollowUps = () => getFollowUps("upcoming");

export const getOverdueFollowUps = () => getFollowUps("overdue");
