import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getHealthMock } = vi.hoisted(() => ({
  getHealthMock: vi.fn(),
}));

vi.mock("@/features/health/services/get-health", () => ({
  getHealth: getHealthMock,
}));

import { HealthStatus } from "@/features/health/components/health-status";

describe("HealthStatus", () => {
  beforeEach(() => {
    getHealthMock.mockReset();
  });

  it("shows loading and then the connected status", async () => {
    getHealthMock.mockResolvedValue({
      status: "ok",
      service: "vibration-api",
    });

    render(<HealthStatus />);

    expect(screen.getByText("確認中...")).toBeVisible();
    expect(await screen.findByText("接続成功")).toBeVisible();
    expect(screen.getByText("ok")).toBeVisible();
    expect(screen.getByText("vibration-api")).toBeVisible();
  });

  it("shows an Error message when the health check fails", async () => {
    getHealthMock.mockRejectedValue(
      new Error("Backend unavailable"),
    );

    await act(async () => {
      render(<HealthStatus />);
    });

    expect(screen.getByText("接続失敗")).toBeVisible();
    expect(screen.getByText("Backend unavailable")).toBeVisible();
  });

  it("uses the fallback message for a non-Error rejection", async () => {
    getHealthMock.mockRejectedValue("failure");

    await act(async () => {
      render(<HealthStatus />);
    });

    expect(
      screen.getByText("不明なエラーが発生しました。"),
    ).toBeVisible();
  });
});
