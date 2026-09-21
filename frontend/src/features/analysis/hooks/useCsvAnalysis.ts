"use client";

import { useCallback, useRef, useState } from "react";
import { generateReport } from "@/features/reports/api/generate-report";
import type { ReportGenerationResponse } from "@/features/reports/types/report";
import { ApiError } from "@/lib/errors/api-error";
import { uploadCsv } from "../api/upload-csv";
import type { CsvAnalysisStatus, CsvUploadInput } from "../types/analysis";

export type CsvAnalysisInput = CsvUploadInput & {
  thresholdValue: number;
  weather: string;
};

type CsvAnalysisState = {
  status: CsvAnalysisStatus;
  result: ReportGenerationResponse | null;
  error: ApiError | null;
};

const initialState: CsvAnalysisState = {
  status: "idle",
  result: null,
  error: null,
};

function toApiError(cause: unknown): ApiError {
  if (cause instanceof ApiError) {
    return cause;
  }

  return new ApiError({
    message: "予期しないエラーが発生しました。",
    status: null,
    detail: null,
    cause,
  });
}

export function useCsvAnalysis() {
  const [state, setState] = useState<CsvAnalysisState>(initialState);
  const isRunningRef = useRef(false);

  const execute = useCallback(async (input: CsvAnalysisInput): Promise<ReportGenerationResponse | null> => {
    if (isRunningRef.current) {
      return null;
    }

    isRunningRef.current = true;
    setState({ status: "uploading", result: null, error: null });

    try {
      const uploadResponse = await uploadCsv({
        file: input.file,
        equipmentId: input.equipmentId,
        measurementDate: input.measurementDate,
        encoding: input.encoding,
      });

      setState((current) => ({ ...current, status: "generating" }));

      const generationResponse = await generateReport({
        uploadedFileId: uploadResponse.uploaded_file.id,
        thresholdValue: input.thresholdValue,
        weather: input.weather,
      });

      setState({ status: "success", result: generationResponse, error: null });

      return generationResponse;
    } catch (cause) {
      setState({ status: "error", result: null, error: toApiError(cause) });

      return null;
    } finally {
      isRunningRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    isRunningRef.current = false;
    setState(initialState);
  }, []);

  const progressMessage =
    state.status === "uploading"
      ? "CSVをアップロードしています..."
      : state.status === "generating"
        ? "AIレポートを生成しています..."
        : null;

  return {
    status: state.status,
    result: state.result,
    error: state.error,
    isPending: state.status === "uploading" || state.status === "generating",
    progressMessage,
    execute,
    reset,
  };
}
