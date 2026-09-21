import { apiRequest } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";
import { ApiError } from "@/lib/errors/api-error";

import type {
  CsvUploadInput,
  FileUploadResponse,
} from "../types/analysis";

export async function uploadCsv(
  input: CsvUploadInput,
): Promise<FileUploadResponse> {
  if (!input.file) {
    throw new ApiError({
      message: "CSVファイルを選択してください。",
      status: null,
      detail: null,
    });
  }

  const equipmentId = input.equipmentId.trim();
  const measurementDate = input.measurementDate.trim();
  const encoding = input.encoding.trim();

  if (!equipmentId) {
    throw new ApiError({
      message: "設備IDを入力してください。",
      status: null,
      detail: null,
    });
  }

  if (!measurementDate) {
    throw new ApiError({
      message: "測定日を入力してください。",
      status: null,
      detail: null,
    });
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(measurementDate)) {
    throw new ApiError({
      message: "測定日はYYYY-MM-DD形式で入力してください。",
      status: null,
      detail: null,
    });
  }

  const parsedMeasurementDate = new Date(
    `${measurementDate}T00:00:00`,
  );

  if (Number.isNaN(parsedMeasurementDate.getTime())) {
    throw new ApiError({
      message: "有効な測定日を入力してください。",
      status: null,
      detail: null,
    });
  }

  if (!encoding) {
    throw new ApiError({
      message: "文字コードを入力してください。",
      status: null,
      detail: null,
    });
  }

  const formData = new FormData();

  formData.append("file", input.file);
  formData.append("equipment_id", equipmentId);
  formData.append("measurement_date", measurementDate);
  formData.append("encoding", encoding);

  return apiRequest<FileUploadResponse>(apiPaths.files, {
    method: "POST",
    formData,
  });
}
