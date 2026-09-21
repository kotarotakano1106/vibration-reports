import { apiRequest } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";
import { ApiError } from "@/lib/errors/api-error";
import type { ReportGenerateInput, ReportGenerationResponse } from "../types/report";

export async function generateReport(input: ReportGenerateInput): Promise<ReportGenerationResponse> {
  if (!input.uploadedFileId.trim()) {
    throw new ApiError({
      message: "アップロード済みCSVのIDが指定されていません。",
      status: null,
      detail: null,
    });
  }

  if (input.thresholdValue <= 0) {
    throw new ApiError({
      message: "異常判定の閾値には0より大きい値を指定してください。",
      status: null,
      detail: null,
    });
  }

  const weather = input.weather && input.weather.trim() ? input.weather.trim() : null;

  return apiRequest<ReportGenerationResponse>(apiPaths.reportGenerate, {
    method: "POST",
    json: {
      uploaded_file_id: input.uploadedFileId,
      threshold_value: input.thresholdValue,
      weather,
    },
  });
}
