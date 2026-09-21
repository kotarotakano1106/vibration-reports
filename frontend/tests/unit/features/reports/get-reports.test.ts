import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiPaths } from "@/lib/api/paths";
import type { ReportListItemResponse } from "@/features/reports/types/report";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest: apiRequestMock,
}));

import { getReports } from "@/features/reports/api/get-reports";

const report: ReportListItemResponse = {
  id: "report-001",
  uploaded_file_id: "file-001",
  equipment_id: "MOTOR-001",
  measurement_date: "2026-09-16",
  title: "MOTOR-001 振動分析レポート",
  anomaly_count: 2,
  status: "requires_attention",
  created_by: "user-001",
  created_at: "2026-09-16T06:00:00Z",
  original_filename: "motor-001.csv",
  threshold_value: 2,
};

describe("getReports", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("requests the reports endpoint and returns the response", async () => {
    apiRequestMock.mockResolvedValue([report]);

    await expect(getReports()).resolves.toEqual([report]);
    expect(apiRequestMock).toHaveBeenCalledOnce();
    expect(apiRequestMock).toHaveBeenCalledWith(apiPaths.reports);
  });

  it("returns an empty report list", async () => {
    apiRequestMock.mockResolvedValue([]);

    await expect(getReports()).resolves.toEqual([]);
    expect(apiRequestMock).toHaveBeenCalledWith(apiPaths.reports);
  });

  it("propagates an API request error", async () => {
    const error = new Error("レポート一覧を取得できませんでした。");
    apiRequestMock.mockRejectedValue(error);

    await expect(getReports()).rejects.toBe(error);
    expect(apiRequestMock).toHaveBeenCalledWith(apiPaths.reports);
  });
});
