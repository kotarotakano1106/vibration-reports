import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { downloadReportPdfMock } = vi.hoisted(() => ({
  downloadReportPdfMock: vi.fn(),
}));

vi.mock("@/features/reports/api/download-report-pdf", () => ({
  downloadReportPdf: downloadReportPdfMock,
}));

import { PdfDownloadButton } from "@/features/reports/components/PdfDownloadButton";

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("PdfDownloadButton", () => {
  beforeEach(() => {
    downloadReportPdfMock.mockReset();
  });

  it("is disabled when a report ID is missing", () => {
    render(<PdfDownloadButton reportId={null} />);

    expect(screen.getByRole("button", { name: "PDF出力" })).toBeDisabled();
  });

  it("downloads the PDF for the specified report", async () => {
    const user = userEvent.setup();
    downloadReportPdfMock.mockResolvedValue(undefined);
    render(<PdfDownloadButton reportId="report-001" />);

    await user.click(screen.getByRole("button", { name: "PDF出力" }));

    expect(downloadReportPdfMock).toHaveBeenCalledOnce();
    expect(downloadReportPdfMock).toHaveBeenCalledWith("report-001");
    expect(screen.getByRole("button", { name: "PDF出力" })).toBeEnabled();
  });

  it("shows a pending state and prevents another click", async () => {
    const user = userEvent.setup();
    const deferred = createDeferred<void>();
    downloadReportPdfMock.mockReturnValue(deferred.promise);
    render(<PdfDownloadButton reportId="report-001" />);

    await user.click(screen.getByRole("button", { name: "PDF出力" }));

    expect(screen.getByRole("button", { name: "PDF生成中..." })).toBeDisabled();
    expect(screen.getByRole("progressbar")).toBeVisible();
    expect(downloadReportPdfMock).toHaveBeenCalledOnce();

    await act(async () => {
      deferred.resolve();
      await deferred.promise;
    });

    expect(screen.getByRole("button", { name: "PDF出力" })).toBeEnabled();
  });

  it("shows an Error message in the tooltip after failure", async () => {
    const user = userEvent.setup();
    downloadReportPdfMock.mockRejectedValue(new Error("PDFを取得できませんでした。"));
    render(<PdfDownloadButton reportId="report-001" />);

    await user.click(screen.getByRole("button", { name: "PDF出力" }));
    await user.hover(screen.getByRole("button", { name: "PDF出力" }));

    expect(await screen.findByRole("tooltip")).toHaveTextContent(
      "PDFを取得できませんでした。",
    );
    expect(screen.getByRole("button", { name: "PDF出力" })).toBeEnabled();
  });

  it("uses the fallback message for a non-Error rejection", async () => {
    const user = userEvent.setup();
    downloadReportPdfMock.mockRejectedValue("unexpected failure");
    render(<PdfDownloadButton reportId="report-001" />);

    await user.click(screen.getByRole("button", { name: "PDF出力" }));
    await user.hover(screen.getByRole("button", { name: "PDF出力" }));

    expect(await screen.findByRole("tooltip")).toHaveTextContent(
      "PDFのダウンロードに失敗しました。",
    );
  });
});
