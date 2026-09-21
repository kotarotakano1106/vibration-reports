export const apiPaths = {
  health: "/health",
  files: "/api/v1/files",
  reports: "/api/v1/reports",
  reportGenerate: "/api/v1/reports/generate",
  search: "/api/v1/search",
  chat: "/api/v1/chat",
  reportPdf: (reportId: string): string =>
    `/api/v1/reports/${encodeURIComponent(reportId)}/pdf`,
  measurements: (
    uploadedFileId: string,
  ): string =>
    `/api/v1/files/${encodeURIComponent(
      uploadedFileId,
    )}/measurements`,
} as const;
