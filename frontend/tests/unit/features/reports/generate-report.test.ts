import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ReportGenerationResponse } from "@/features/reports/types/report";
import { ApiError } from "@/lib/errors/api-error";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest: apiRequestMock,
}));

import { generateReport } from "@/features/reports/api/generate-report";

const response = {
  message: "AIレポートを生成しました。",
  report: {
    id: "report-001",
    uploaded_file_id: "file-001",
    created_by: "user-001",
    equipment_id: "MOTOR-001",
    measurement_date: "2026-09-16",
    weather: "晴れ",
    title: "MOTOR-001 振動分析レポート",
    record_count: 2,
    minimum_value: 1.5,
    maximum_value: 2.5,
    average_value: 2,
    median_value: 2,
    standard_deviation: 0.5,
    threshold_value: 2,
    anomaly_count: 1,
    anomaly_details: [],
    status: "requires_attention",
    ai_summary: "要点",
    ai_analysis: "分析",
    recommendation: "点検してください。",
    report_text: "レポート本文",
    ai_model: "chat-model",
    prompt_version: "v1",
    chart_path: null,
    pdf_path: null,
    pdf_generated_at: null,
    created_at: "2026-09-16T09:00:00+09:00",
    updated_at: "2026-09-16T09:00:00+09:00",
  },
  analysis: {
    record_count: 2,
    minimum_value: 1.5,
    maximum_value: 2.5,
    average_value: 2,
    median_value: 2,
    standard_deviation: 0.5,
    threshold_value: 2,
    anomaly_count: 1,
    anomaly_rate: 0.5,
    status: "requires_attention",
    anomalies: [],
  },
  report_chunk_id: "chunk-001",
  embedding_model: "embedding-model",
  embedding_dimensions: 1536,
} satisfies ReportGenerationResponse;

describe("generateReport", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("posts the report generation request and returns the response", async () => {
    apiRequestMock.mockResolvedValue(response);

    await expect(
      generateReport({
        uploadedFileId: "file-001",
        thresholdValue: 2,
        weather: "晴れ",
      }),
    ).resolves.toEqual(response);

    expect(apiRequestMock).toHaveBeenCalledOnce();
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/reports/generate",
      {
        method: "POST",
        json: {
          uploaded_file_id: "file-001",
          threshold_value: 2,
          weather: "晴れ",
        },
      },
    );
  });

  it("trims the weather value", async () => {
    apiRequestMock.mockResolvedValue(response);

    await generateReport({
      uploadedFileId: "file-001",
      thresholdValue: 2.5,
      weather: "  曇り  ",
    });

    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/reports/generate",
      expect.objectContaining({
        json: {
          uploaded_file_id: "file-001",
          threshold_value: 2.5,
          weather: "曇り",
        },
      }),
    );
  });

  it.each([null, "", "   "])(
    "normalizes an empty weather value to null: %s",
    async (weather) => {
      apiRequestMock.mockResolvedValue(response);

      await generateReport({
        uploadedFileId: "file-001",
        thresholdValue: 2,
        weather,
      });

      expect(apiRequestMock).toHaveBeenCalledWith(
        "/api/v1/reports/generate",
        expect.objectContaining({
          json: {
            uploaded_file_id: "file-001",
            threshold_value: 2,
            weather: null,
          },
        }),
      );
    },
  );

  it("rejects a blank uploaded file ID without calling the API", async () => {
    await expect(
      generateReport({
        uploadedFileId: "   ",
        thresholdValue: 2,
        weather: null,
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: null,
      detail: null,
      message: "アップロード済みCSVのIDが指定されていません。",
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it.each([0, -1])(
    "rejects a non-positive threshold value: %s",
    async (thresholdValue) => {
      await expect(
        generateReport({
          uploadedFileId: "file-001",
          thresholdValue,
          weather: null,
        }),
      ).rejects.toMatchObject({
        name: "ApiError",
        status: null,
        detail: null,
        message: "異常判定の閾値には0より大きい値を指定してください。",
      });

      expect(apiRequestMock).not.toHaveBeenCalled();
    },
  );

  it("propagates an API request error", async () => {
    const error = ApiError.fromHttpStatus(
      409,
      "同一内容のレポートがすでに登録されています。",
    );
    apiRequestMock.mockRejectedValue(error);

    await expect(
      generateReport({
        uploadedFileId: "file-001",
        thresholdValue: 2,
        weather: null,
      }),
    ).rejects.toBe(error);
  });
});
