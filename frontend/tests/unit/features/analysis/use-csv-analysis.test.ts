import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FileUploadResponse } from "@/features/analysis/types/analysis";
import type { ReportGenerationResponse } from "@/features/reports/types/report";
import { ApiError } from "@/lib/errors/api-error";

const { generateReportMock, uploadCsvMock } = vi.hoisted(() => ({
  generateReportMock: vi.fn(),
  uploadCsvMock: vi.fn(),
}));

vi.mock("@/features/analysis/api/upload-csv", () => ({
  uploadCsv: uploadCsvMock,
}));

vi.mock("@/features/reports/api/generate-report", () => ({
  generateReport: generateReportMock,
}));

import { useCsvAnalysis } from "@/features/analysis/hooks/useCsvAnalysis";

const file = new File(
  ["measured_at,vibration_value\n2026-09-18T09:00:00,1.5"],
  "measurement.csv",
  { type: "text/csv" },
);

const input = {
  file,
  equipmentId: "MOTOR-001",
  measurementDate: "2026-09-18",
  encoding: "UTF-8",
  thresholdValue: 2,
  weather: "晴れ",
};

const uploadResponse: FileUploadResponse = {
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
};

const generationResponse = {
  message: "AIレポートを生成しました。",
  report: {
    id: "report-001",
    uploaded_file_id: "file-001",
    created_by: "user-001",
    equipment_id: "MOTOR-001",
    measurement_date: "2026-09-18",
    weather: "晴れ",
    title: "MOTOR-001 振動分析レポート",
    record_count: 1,
    minimum_value: 1.5,
    maximum_value: 1.5,
    average_value: 1.5,
    median_value: 1.5,
    standard_deviation: 0,
    threshold_value: 2,
    anomaly_count: 0,
    anomaly_details: [],
    status: "normal",
    ai_summary: "正常です。",
    ai_analysis: "異常はありません。",
    recommendation: null,
    report_text: "レポート本文",
    ai_model: "chat-model",
    prompt_version: "v1",
    chart_path: null,
    pdf_path: null,
    pdf_generated_at: null,
    created_at: "2026-09-18T09:00:00+09:00",
    updated_at: "2026-09-18T09:00:00+09:00",
  },
  analysis: {
    record_count: 1,
    minimum_value: 1.5,
    maximum_value: 1.5,
    average_value: 1.5,
    median_value: 1.5,
    standard_deviation: 0,
    threshold_value: 2,
    anomaly_count: 0,
    anomaly_rate: 0,
    status: "normal",
    anomalies: [],
  },
  report_chunk_id: "chunk-001",
  embedding_model: "embedding-model",
  embedding_dimensions: 1536,
} satisfies ReportGenerationResponse;

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

describe("useCsvAnalysis", () => {
  beforeEach(() => {
    uploadCsvMock.mockReset();
    generateReportMock.mockReset();
  });

  it("starts with the idle state", () => {
    const { result } = renderHook(() => useCsvAnalysis());

    expect(result.current.status).toBe("idle");
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
    expect(result.current.progressMessage).toBeNull();
  });

  it("shows uploading and generating progress before success", async () => {
    const uploadDeferred = createDeferred<FileUploadResponse>();
    const generationDeferred = createDeferred<ReportGenerationResponse>();
    uploadCsvMock.mockReturnValue(uploadDeferred.promise);
    generateReportMock.mockReturnValue(generationDeferred.promise);
    const { result } = renderHook(() => useCsvAnalysis());

    let executePromise!: Promise<ReportGenerationResponse | null>;
    act(() => {
      executePromise = result.current.execute(input);
    });

    expect(result.current.status).toBe("uploading");
    expect(result.current.isPending).toBe(true);
    expect(result.current.progressMessage).toBe(
      "CSVをアップロードしています...",
    );
    expect(uploadCsvMock).toHaveBeenCalledWith({
      file,
      equipmentId: "MOTOR-001",
      measurementDate: "2026-09-18",
      encoding: "UTF-8",
    });

    await act(async () => {
      uploadDeferred.resolve(uploadResponse);
      await Promise.resolve();
    });

    expect(result.current.status).toBe("generating");
    expect(result.current.isPending).toBe(true);
    expect(result.current.progressMessage).toBe(
      "AIレポートを生成しています...",
    );
    expect(generateReportMock).toHaveBeenCalledWith({
      uploadedFileId: "file-001",
      thresholdValue: 2,
      weather: "晴れ",
    });

    await act(async () => {
      generationDeferred.resolve(generationResponse);
      await expect(executePromise).resolves.toEqual(generationResponse);
    });

    expect(result.current.status).toBe("success");
    expect(result.current.result).toEqual(generationResponse);
    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
    expect(result.current.progressMessage).toBeNull();
  });

  it("stores an upload ApiError and skips report generation", async () => {
    const error = ApiError.fromHttpStatus(400, "CSVファイルが不正です。");
    uploadCsvMock.mockRejectedValue(error);
    const { result } = renderHook(() => useCsvAnalysis());

    await act(async () => {
      await expect(result.current.execute(input)).resolves.toBeNull();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe(error);
    expect(result.current.isPending).toBe(false);
    expect(generateReportMock).not.toHaveBeenCalled();
  });

  it("stores a report generation ApiError", async () => {
    const error = ApiError.fromHttpStatus(
      502,
      "AIレポートの生成に失敗しました。",
    );
    uploadCsvMock.mockResolvedValue(uploadResponse);
    generateReportMock.mockRejectedValue(error);
    const { result } = renderHook(() => useCsvAnalysis());

    await act(async () => {
      await expect(result.current.execute(input)).resolves.toBeNull();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe(error);
    expect(result.current.isPending).toBe(false);
  });

  it("converts a non-ApiError failure to the fallback ApiError", async () => {
    const cause = new TypeError("unexpected failure");
    uploadCsvMock.mockRejectedValue(cause);
    const { result } = renderHook(() => useCsvAnalysis());

    await act(async () => {
      await result.current.execute(input);
    });

    expect(result.current.error).toBeInstanceOf(ApiError);
    expect(result.current.error).toMatchObject({
      status: null,
      detail: null,
      message: "予期しないエラーが発生しました。",
      cause,
    });
  });

  it("prevents a second execution while processing", async () => {
    const deferred = createDeferred<FileUploadResponse>();
    uploadCsvMock.mockReturnValue(deferred.promise);
    generateReportMock.mockResolvedValue(generationResponse);
    const { result } = renderHook(() => useCsvAnalysis());

    let firstPromise!: Promise<ReportGenerationResponse | null>;
    act(() => {
      firstPromise = result.current.execute(input);
    });

    let secondResult!: ReportGenerationResponse | null;
    await act(async () => {
      secondResult = await result.current.execute(input);
    });

    expect(secondResult).toBeNull();
    expect(uploadCsvMock).toHaveBeenCalledOnce();

    await act(async () => {
      deferred.resolve(uploadResponse);
      await expect(firstPromise).resolves.toEqual(generationResponse);
    });
  });

  it("reset restores the initial state after success", async () => {
    uploadCsvMock.mockResolvedValue(uploadResponse);
    generateReportMock.mockResolvedValue(generationResponse);
    const { result } = renderHook(() => useCsvAnalysis());

    await act(async () => {
      await result.current.execute(input);
    });

    expect(result.current.status).toBe("success");

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
    expect(result.current.progressMessage).toBeNull();
  });
});
