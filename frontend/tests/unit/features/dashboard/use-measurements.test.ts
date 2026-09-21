import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { MeasurementDataResponse } from "@/features/dashboard/types/measurement";
import { ApiError } from "@/lib/errors/api-error";

const { getMeasurementsMock } = vi.hoisted(() => ({
  getMeasurementsMock: vi.fn(),
}));

vi.mock("@/features/dashboard/api/get-measurements", () => ({
  getMeasurements: getMeasurementsMock,
}));

import { useMeasurements } from "@/features/dashboard/hooks/useMeasurements";

const input = {
  uploadedFileId: "file-001",
  thresholdValue: 2,
};

const response: MeasurementDataResponse = {
  uploaded_file_id: "file-001",
  equipment_id: "MOTOR-001",
  measurement_date: "2026-09-18",
  measurement_count: 2,
  threshold_value: 2,
  measurements: [
    {
      measured_at: "2026-09-18T09:00:00+09:00",
      vibration_value: 1.5,
      is_anomaly: false,
    },
    {
      measured_at: "2026-09-18T09:01:00+09:00",
      vibration_value: 2.5,
      is_anomaly: true,
    },
  ],
};

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

describe("useMeasurements", () => {
  beforeEach(() => {
    getMeasurementsMock.mockReset();
  });

  it("starts with the idle state", () => {
    const { result } = renderHook(() => useMeasurements());

    expect(result.current.status).toBe("idle");
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("sets loading state and stores a successful response", async () => {
    const deferred = createDeferred<MeasurementDataResponse>();
    getMeasurementsMock.mockReturnValue(deferred.promise);
    const { result } = renderHook(() => useMeasurements());

    let loadPromise!: Promise<MeasurementDataResponse | null>;
    act(() => {
      loadPromise = result.current.load(input);
    });

    expect(result.current.status).toBe("loading");
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(getMeasurementsMock).toHaveBeenCalledWith(input);

    await act(async () => {
      deferred.resolve(response);
      await expect(loadPromise).resolves.toEqual(response);
    });

    expect(result.current.status).toBe("success");
    expect(result.current.data).toEqual(response);
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("stores an ApiError and returns null", async () => {
    const error = ApiError.fromHttpStatus(
      404,
      "測定データが見つかりません。",
    );
    getMeasurementsMock.mockRejectedValue(error);
    const { result } = renderHook(() => useMeasurements());

    await act(async () => {
      await expect(result.current.load(input)).resolves.toBeNull();
    });

    expect(result.current.status).toBe("error");
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(error);
    expect(result.current.isLoading).toBe(false);
  });

  it("converts an unexpected failure to ApiError", async () => {
    const cause = new TypeError("unexpected failure");
    getMeasurementsMock.mockRejectedValue(cause);
    const { result } = renderHook(() => useMeasurements());

    await act(async () => {
      await result.current.load(input);
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBeInstanceOf(ApiError);
    expect(result.current.error).toMatchObject({
      status: null,
      detail: null,
      message: "測定データの取得中に予期しないエラーが発生しました。",
      cause,
    });
  });

  it("prevents a second load while a request is running", async () => {
    const deferred = createDeferred<MeasurementDataResponse>();
    getMeasurementsMock.mockReturnValue(deferred.promise);
    const { result } = renderHook(() => useMeasurements());

    let firstPromise!: Promise<MeasurementDataResponse | null>;
    let secondResult!: MeasurementDataResponse | null;

    act(() => {
      firstPromise = result.current.load(input);
    });

    await act(async () => {
      secondResult = await result.current.load({
        uploadedFileId: "file-002",
        thresholdValue: 3,
      });
    });

    expect(secondResult).toBeNull();
    expect(getMeasurementsMock).toHaveBeenCalledOnce();
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      deferred.resolve(response);
      await firstPromise;
    });

    expect(result.current.status).toBe("success");
  });

  it("reset restores the initial state after success", async () => {
    getMeasurementsMock.mockResolvedValue(response);
    const { result } = renderHook(() => useMeasurements());

    await act(async () => {
      await result.current.load(input);
    });

    expect(result.current.status).toBe("success");

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("reset allows another load while the prior promise is unresolved", async () => {
    const first = createDeferred<MeasurementDataResponse>();
    getMeasurementsMock
      .mockReturnValueOnce(first.promise)
      .mockResolvedValueOnce(response);
    const { result } = renderHook(() => useMeasurements());

    let firstPromise!: Promise<MeasurementDataResponse | null>;
    act(() => {
      firstPromise = result.current.load(input);
    });

    act(() => {
      result.current.reset();
    });

    await act(async () => {
      await expect(result.current.load(input)).resolves.toEqual(response);
    });

    expect(getMeasurementsMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      first.resolve(response);
      await firstPromise;
    });
  });
});
