import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FileUploadResponse } from "@/features/analysis/types/analysis";
import { ApiError } from "@/lib/errors/api-error";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  apiRequest: apiRequestMock,
}));

import { uploadCsv } from "@/features/analysis/api/upload-csv";

const response = {
  message: "CSVファイルをアップロードしました。",
  is_duplicate: false,
  uploaded_file: {
    id: "file-001",
    uploaded_by: "user-001",
    equipment_id: "MOTOR-001",
    original_filename: "measurement.csv",
    stored_filename: "stored.csv",
    file_path: "uploads/stored.csv",
    file_size: 32,
    mime_type: "text/csv",
    encoding: "UTF-8",
    checksum: "checksum-001",
    measurement_date: "2026-09-18",
    status: "uploaded",
    error_code: null,
    error_message: null,
    uploaded_at: "2026-09-18T09:00:00+09:00",
    updated_at: "2026-09-18T09:00:00+09:00",
  },
} satisfies FileUploadResponse;

function createCsvFile(): File {
  return new File(
    ["measured_at,vibration_value\n2026-09-18T09:00:00,1.5"],
    "measurement.csv",
    { type: "text/csv" },
  );
}

describe("uploadCsv", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
  });

  it("builds FormData and uploads the CSV", async () => {
    const file = createCsvFile();
    apiRequestMock.mockResolvedValue(response);

    await expect(
      uploadCsv({
        file,
        equipmentId: "  MOTOR-001  ",
        measurementDate: "  2026-09-18  ",
        encoding: "  UTF-8  ",
      }),
    ).resolves.toEqual(response);

    expect(apiRequestMock).toHaveBeenCalledOnce();
    expect(apiRequestMock).toHaveBeenCalledWith(
      "/api/v1/files",
      expect.objectContaining({
        method: "POST",
        formData: expect.any(FormData),
      }),
    );

    const options = apiRequestMock.mock.calls[0][1] as {
      formData: FormData;
    };
    expect(options.formData.get("file")).toBe(file);
    expect(options.formData.get("equipment_id")).toBe("MOTOR-001");
    expect(options.formData.get("measurement_date")).toBe("2026-09-18");
    expect(options.formData.get("encoding")).toBe("UTF-8");
  });

  it("rejects a missing file without calling the API", async () => {
    await expect(
      uploadCsv({
        file: null as unknown as File,
        equipmentId: "MOTOR-001",
        measurementDate: "2026-09-18",
        encoding: "UTF-8",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "CSVファイルを選択してください。",
      status: null,
      detail: null,
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("rejects a blank equipment ID without calling the API", async () => {
    await expect(
      uploadCsv({
        file: createCsvFile(),
        equipmentId: "   ",
        measurementDate: "2026-09-18",
        encoding: "UTF-8",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "設備IDを入力してください。",
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("rejects a blank measurement date", async () => {
    await expect(
      uploadCsv({
        file: createCsvFile(),
        equipmentId: "MOTOR-001",
        measurementDate: "   ",
        encoding: "UTF-8",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "測定日を入力してください。",
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it.each(["2026/09/18", "18-09-2026", "2026-9-18"])(
    "rejects a measurement date with an invalid format: %s",
    async (measurementDate) => {
      await expect(
        uploadCsv({
          file: createCsvFile(),
          equipmentId: "MOTOR-001",
          measurementDate,
          encoding: "UTF-8",
        }),
      ).rejects.toMatchObject({
        name: "ApiError",
        message: "測定日はYYYY-MM-DD形式で入力してください。",
      });

      expect(apiRequestMock).not.toHaveBeenCalled();
    },
  );

  it("rejects an invalid calendar date", async () => {
    await expect(
      uploadCsv({
        file: createCsvFile(),
        equipmentId: "MOTOR-001",
        measurementDate: "2026-99-99",
        encoding: "UTF-8",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "有効な測定日を入力してください。",
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("rejects a blank encoding", async () => {
    await expect(
      uploadCsv({
        file: createCsvFile(),
        equipmentId: "MOTOR-001",
        measurementDate: "2026-09-18",
        encoding: "   ",
      }),
    ).rejects.toMatchObject({
      name: "ApiError",
      message: "文字コードを入力してください。",
    });

    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("propagates an API request error", async () => {
    const error = ApiError.fromHttpStatus(409, "同一ファイルが存在します。");
    apiRequestMock.mockRejectedValue(error);

    await expect(
      uploadCsv({
        file: createCsvFile(),
        equipmentId: "MOTOR-001",
        measurementDate: "2026-09-18",
        encoding: "UTF-8",
      }),
    ).rejects.toBe(error);
  });
});
