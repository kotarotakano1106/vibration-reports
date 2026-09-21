import { buildApiUrl } from "@/lib/api/client";
import { apiPaths } from "@/lib/api/paths";
import { ApiError, parseErrorDetail } from "@/lib/errors/api-error";

export async function downloadReportPdf(
  reportId: string,
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(
      buildApiUrl(apiPaths.reportPdf(reportId)),
      {
        method: "GET",
        headers: { Accept: "application/pdf" },
        cache: "no-store",
      },
    );
  } catch (cause) {
    throw ApiError.networkError(cause);
  }

  if (!response.ok) {
    const text = await response.text();
    let detail: string | null = text || null;
    try {
      detail = text ? parseErrorDetail(JSON.parse(text)) : null;
    } catch {
      // JSON以外のエラー本文はそのまま使用する。
    }
    throw ApiError.fromHttpStatus(response.status, detail);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition");
  const matched = disposition?.match(/filename="?([^";]+)"?/i);
  const filename = matched?.[1] ?? `vibration-report_${reportId}.pdf`;

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
