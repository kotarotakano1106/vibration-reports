import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MeasurementDataResponse } from "@/features/dashboard/types/measurement";
import { ApiError } from "@/lib/errors/api-error";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest: apiRequestMock,
}));

import { getMeasurements } from "@/features/dashboard/api/get-measurements";

const response: MeasurementDataResponse = {
  uploaded_file_id: "file-001",
  equipment_id: "MOTOR-001",
  measurement_date: "2026-09-16",
  measurement_count: 2,
  threshold_value: 2,
  measurements: [
    {
      measured_at: "2026-09-16T09:00:00+09:00",
      vibration_value: 1.5,
      is_anomaly: false,
    },
    {
      measured_at: "2026-09-16T09:01:00+09:00",
      vibration_value: 2.5,
      is_anomaly: true,
    },
  ],
};

describe("getMeasurements", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("trims the uploaded file ID and requests measurements", async () => {
    apiRequestMock.mockResolvedValue(response);

    await expect(
      getMeasurements({
        uploadedFileId: "  file-001  ",
        thresholdValue: 2,
      }),
    ).resolves.toEqual(response);

    expect(apiRequestMock).toHaveBeenCalledOnce();
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/files/file-001/measurements?threshold_value=2",
      {
        method: "GET",
        signal: undefined,
      },
    );
  });

  it("encodes the uploaded file ID", async () => {
    apiRequestMock.mockResolvedValue(response);

    await getMeasurements({
      uploadedFileId: "file/id with spaces",
      thresholdValue: 2.5,
    });

    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/files/file%2Fid%20with%20spaces/measurements?threshold_value=2.5",
      expect.any(Object),
    );
  });

  it("passes an AbortSignal to apiRequest", async () => {
    apiRequestMock.mockResolvedValue(response);
    const controller = new AbortController();

    await getMeasurements(
      {
        uploadedFileId: "file-001",
        thresholdValue: 2,
      },
      controller.signal,
    );

    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/files/file-001/measurements?threshold_value=2",
      {
        method: "GET",
        signal: controller.signal,
      },
    );
  });

  it("rejects a blank uploaded file ID without calling the API", async () => {
    const promise = getMeasurements({
      uploadedFileId: "   ",
      thresholdValue: 2,
    });

    await expect(promise).rejects.toMatchObject({
      name: "ApiError",
      status: null,
      detail: null,
      message: "アップロード済みCSVのIDが指定されていません。",
    });
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY])(
    "rejects an invalid threshold value: %s",
    async (thresholdValue) => {
      const promise = getMeasurements({
        uploadedFileId: "file-001",
        thresholdValue,
      });

      await expect(promise).rejects.toMatchObject({
        name: "ApiError",
        status: null,
        detail: null,
        message: "異常判定の閾値には0より大きい数値を指定してください。",
      });
      expect(apiRequestMock).not.toHaveBeenCalled();
    },
  );

  it("propagates an API request error", async () => {
    const error = ApiError.fromHttpStatus(
      404,
      "測定データが見つかりません。",
    );
    apiRequestMock.mockRejectedValue(error);

    await expect(
      getMeasurements({
        uploadedFileId: "file-001",
        thresholdValue: 2,
      }),
    ).rejects.toBe(error);
  });
});
