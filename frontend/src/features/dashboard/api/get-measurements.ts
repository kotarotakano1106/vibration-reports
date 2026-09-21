import { apiRequest } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";
import { ApiError } from "@/lib/errors/api-error";

import type {
  GetMeasurementsInput,
  MeasurementDataResponse,
} from "../types/measurement";


export async function getMeasurements(
  input: GetMeasurementsInput,
  signal?: AbortSignal,
): Promise<MeasurementDataResponse> {
  const uploadedFileId =
    input.uploadedFileId.trim();

  if (!uploadedFileId) {
    throw new ApiError({
      message: (
        "アップロード済みCSVのIDが"
        + "指定されていません。"
      ),
      status: null,
      detail: null,
    });
  }

  if (
    !Number.isFinite(input.thresholdValue)
    || input.thresholdValue <= 0
  ) {
    throw new ApiError({
      message: (
        "異常判定の閾値には"
        + "0より大きい数値を"
        + "指定してください。"
      ),
      status: null,
      detail: null,
    });
  }

  const query = new URLSearchParams({
    threshold_value:
      String(input.thresholdValue),
  });

  const path = (
    `${apiPaths.measurements(
      uploadedFileId,
    )}?${query.toString()}`
  );

  return apiRequest<MeasurementDataResponse>(
    path,
    {
      method: "GET",
      signal,
    },
  );
}