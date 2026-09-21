import { describe, expect, it } from "vitest";

import { apiPaths } from "@/lib/api/paths";

describe("apiPaths", () => {
  it("defines the static API paths", () => {
    expect(apiPaths.health).toBe("/health");
    expect(apiPaths.files).toBe("/api/v1/files");
    expect(apiPaths.reports).toBe("/api/v1/reports");
    expect(apiPaths.reportGenerate).toBe("/api/v1/reports/generate");
    expect(apiPaths.search).toBe("/api/v1/search");
    expect(apiPaths.chat).toBe("/api/v1/chat");
  });

  it("encodes a report ID used in the PDF path", () => {
    expect(apiPaths.reportPdf("report/id with spaces")).toBe(
      "/api/v1/reports/report%2Fid%20with%20spaces/pdf",
    );
  });

  it("encodes an uploaded file ID used in the measurements path", () => {
    expect(apiPaths.measurements("file/id with spaces")).toBe(
      "/api/v1/files/file%2Fid%20with%20spaces/measurements",
    );
  });
});
