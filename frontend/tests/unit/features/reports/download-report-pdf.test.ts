import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { downloadReportPdf } from "@/features/reports/api/download-report-pdf";
import { ApiError } from "@/lib/errors/api-error";

const originalBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

describe("downloadReportPdf", () => {
  const createObjectUrlMock = vi.fn(() => "blob:report-pdf");
  const revokeObjectUrlMock = vi.fn();
  let clickSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: createObjectUrlMock,
      revokeObjectURL: revokeObjectUrlMock,
    });
    clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    createObjectUrlMock.mockClear();
    revokeObjectUrlMock.mockClear();
    clickSpy.mockRestore();
    document.body.replaceChildren();

    if (originalBaseUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalBaseUrl;
    }
  });

  it("downloads the PDF using the response filename", async () => {
    const pdf = new Blob(["pdf-content"], { type: "application/pdf" });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(pdf, {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": 'attachment; filename="report-001.pdf"',
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await downloadReportPdf("report-001");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/reports/report-001/pdf",
      {
        method: "GET",
        headers: { Accept: "application/pdf" },
        cache: "no-store",
      },
    );
    expect(createObjectUrlMock).toHaveBeenCalledOnce();
    expect(clickSpy).toHaveBeenCalledOnce();
    expect(clickSpy.mock.instances[0]).toMatchObject({
      href: "blob:report-pdf",
      download: "report-001.pdf",
    });
    expect(revokeObjectUrlMock).toHaveBeenCalledWith("blob:report-pdf");
    expect(document.querySelector("a")).toBeNull();
  });

  it("encodes the report ID and uses the fallback filename", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(new Blob(["pdf"]), {
          status: 200,
          headers: { "Content-Type": "application/pdf" },
        }),
      ),
    );

    await downloadReportPdf("report/id with spaces");

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/reports/report%2Fid%20with%20spaces/pdf",
      expect.any(Object),
    );
    expect(clickSpy.mock.instances[0]).toMatchObject({
      download: "vibration-report_report/id with spaces.pdf",
    });
  });

  it("converts a JSON HTTP error to ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "PDFが見つかりません。" }), {
          status: 404,
        }),
      ),
    );

    const error = await downloadReportPdf("missing").catch(
      (caught) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      detail: "PDFが見つかりません。",
      message: "PDFが見つかりません。",
    });
    expect(createObjectUrlMock).not.toHaveBeenCalled();
  });

  it("uses plain text from a non-JSON HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("Service unavailable", { status: 503 }),
      ),
    );

    await expect(downloadReportPdf("report-001")).rejects.toMatchObject({
      status: 503,
      detail: "Service unavailable",
      message: "Service unavailable",
    });
  });

  it("converts a fetch failure to a network ApiError", async () => {
    const cause = new TypeError("Failed to fetch");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(cause));

    const error = await downloadReportPdf("report-001").catch(
      (caught) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: null,
      detail: null,
      cause,
    });
  });
});
