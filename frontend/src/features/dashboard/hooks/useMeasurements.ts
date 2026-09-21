"use client";

import {
  useCallback,
  useRef,
  useState,
} from "react";

import { getMeasurements } from "../api/get-measurements";
import type {
  GetMeasurementsInput,
  MeasurementDataResponse,
} from "../types/measurement";

import { ApiError } from "@/lib/errors/api-error";


type MeasurementLoadStatus =
  | "idle"
  | "loading"
  | "success"
  | "error";


type MeasurementState = {
  status: MeasurementLoadStatus;
  data: MeasurementDataResponse | null;
  error: ApiError | null;
};


const initialState: MeasurementState = {
  status: "idle",
  data: null,
  error: null,
};


function toApiError(cause: unknown): ApiError {
  if (cause instanceof ApiError) {
    return cause;
  }

  return new ApiError({
    message: (
      "測定データの取得中に"
      + "予期しないエラーが発生しました。"
    ),
    status: null,
    detail: null,
    cause,
  });
}


export function useMeasurements() {
  const [state, setState] =
    useState<MeasurementState>(
      initialState,
    );

  const isRunningRef = useRef(false);

  const load = useCallback(
    async (
      input: GetMeasurementsInput,
    ): Promise<MeasurementDataResponse | null> => {
      if (isRunningRef.current) {
        return null;
      }

      isRunningRef.current = true;

      setState({
        status: "loading",
        data: null,
        error: null,
      });

      try {
        const response =
          await getMeasurements(input);

        setState({
          status: "success",
          data: response,
          error: null,
        });

        return response;
      } catch (cause) {
        const apiError = toApiError(cause);

        setState({
          status: "error",
          data: null,
          error: apiError,
        });

        return null;
      } finally {
        isRunningRef.current = false;
      }
    },
    [],
  );

  const reset = useCallback(() => {
    isRunningRef.current = false;
    setState(initialState);
  }, []);

  return {
    status: state.status,
    data: state.data,
    error: state.error,
    isLoading: state.status === "loading",
    load,
    reset,
  };
}