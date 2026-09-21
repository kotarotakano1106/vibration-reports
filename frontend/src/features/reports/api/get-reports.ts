import { apiRequest } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";
import type { ReportListItemResponse } from "../types/report";
export async function getReports(): Promise<ReportListItemResponse[]> {
  return apiRequest<ReportListItemResponse[]>(apiPaths.reports);
}
