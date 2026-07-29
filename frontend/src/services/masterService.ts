import API from "../api/caseApi";
import type {
  MasterKey,
  MasterListParams,
  MasterPageResponseMap,
  MasterPayloadMap,
  MasterRecord,
  MasterRecordMap,
  PageResponse,
} from "../types/master";

function toErrorMessage(error: unknown): Error {
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
      : "Something went wrong while processing your request.";

  return new Error(message);
}

function routeFor(master: MasterKey) {
  switch (master) {
    case "banks":
      return "/masters/banks";
    case "branches":
      return "/masters/branches";
    case "executives":
      return "/masters/executives";
    case "loan-types":
      return "/masters/loan-types";
    case "product-types":
      return "/masters/product-types";
    default:
      return "/masters/banks";
  }
}

function buildParams(params: MasterListParams = {}) {
  return {
    ...(params.search ? { search: params.search } : {}),
    ...(typeof params.page === "number" ? { page: params.page } : {}),
    ...(typeof params.pageSize === "number" ? { page_size: params.pageSize } : {}),
    ...(params.all ? { all: true } : {}),
    ...(typeof params.bankId === "number" ? { bank_id: params.bankId } : {}),
    ...(params.statusFilter ? { status_filter: params.statusFilter } : {}),
    ...(params.activeOnly ? { active_only: true } : {}),
  };
}

function normalizeMasterPageResponse<K extends MasterKey>(
  data: unknown,
): MasterPageResponseMap[K] {
  const page = data as Partial<PageResponse<MasterRecord>> | null | undefined;
  const items = Array.isArray(page?.items) ? page.items : [];

  return {
    items,
    total: typeof page?.total === "number" ? page.total : items.length,
    page: typeof page?.page === "number" ? page.page : 1,
    page_size: typeof page?.page_size === "number" ? page.page_size : items.length,
    total_pages: typeof page?.total_pages === "number" ? page.total_pages : 1,
  } as MasterPageResponseMap[K];
}

export async function listMasters<K extends MasterKey>(
  master: K,
  params: MasterListParams = {},
): Promise<MasterPageResponseMap[K]> {
  try {
    const response = await API.get<MasterPageResponseMap[K]>(routeFor(master), {
      params: buildParams(params),
    });

    return normalizeMasterPageResponse<K>(response.data);
  } catch (error) {
    throw toErrorMessage(error);
  }
}

export async function getMasterRecord<K extends MasterKey>(
  master: K,
  id: number,
): Promise<MasterRecordMap[K]> {
  try {
    const response = await API.get<MasterRecordMap[K]>(`${routeFor(master)}/${id}`);
    return response.data;
  } catch (error) {
    throw toErrorMessage(error);
  }
}

export async function createMasterRecord<K extends MasterKey>(
  master: K,
  payload: MasterPayloadMap[K],
): Promise<MasterRecordMap[K]> {
  try {
    const response = await API.post<MasterRecordMap[K]>(routeFor(master), payload);
    return response.data;
  } catch (error) {
    throw toErrorMessage(error);
  }
}

export async function updateMasterRecord<K extends MasterKey>(
  master: K,
  id: number,
  payload: Partial<MasterPayloadMap[K]>,
): Promise<MasterRecordMap[K]> {
  try {
    const response = await API.put<MasterRecordMap[K]>(`${routeFor(master)}/${id}`, payload);
    return response.data;
  } catch (error) {
    throw toErrorMessage(error);
  }
}

export async function deleteMasterRecord<K extends MasterKey>(
  master: K,
  id: number,
): Promise<{ message: string }> {
  try {
    const response = await API.delete<{ message: string }>(`${routeFor(master)}/${id}`);
    return response.data;
  } catch (error) {
    throw toErrorMessage(error);
  }
}
