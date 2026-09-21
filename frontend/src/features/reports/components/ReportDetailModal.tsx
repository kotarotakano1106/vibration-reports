import {
  Box,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import type {
  Report,
  ReportGenerationResponse,
} from "../types/report";
import { PdfDownloadButton } from "./PdfDownloadButton";

type ReportDetailModalProps = {
  report: Report | null;
  generatedReport: ReportGenerationResponse | null;
  onClose: () => void;
};

type StatusPresentation = {
  label: string;
  color: "error" | "warning" | "success" | "default";
};

type StatisticItem = {
  label: string;
  value: string;
};

function getStatusPresentation(status: string): StatusPresentation {
  switch (status) {
    case "requires_attention":
    case "異常":
      return { label: "要確認", color: "error" };
    case "warning":
    case "注意":
      return { label: "注意", color: "warning" };
    case "normal":
    case "正常":
      return { label: "正常", color: "success" };
    default:
      return { label: status || "未設定", color: "default" };
  }
}

function formatNullable(
  value: string | number | null | undefined,
): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value);
}

function formatNumber(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "-";
  }

  return value.toFixed(digits);
}

function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "-";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function formatMeasuredAt(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function normalizeAnalysisLines(value: string): string[] {
  return value
    .replaceAll("<br>", "\n")
    .replaceAll("<br/>", "\n")
    .replaceAll("<br />", "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function AnalysisContent({ text }: { text: string }) {
  const lines = normalizeAnalysisLines(text);

  if (lines.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        AI分析はありません。
      </Typography>
    );
  }

  return (
    <Stack spacing={1}>
      {lines.map((line, index) => {
        if (line.startsWith("## ")) {
          return (
            <Typography
              key={`${line}-${index}`}
              variant="subtitle2"
              color="primary.dark"
              sx={{ fontWeight: 700, mt: index === 0 ? 0 : 0.5 }}
            >
              {line.slice(3)}
            </Typography>
          );
        }

        if (line.startsWith("- ")) {
          return (
            <Stack
              key={`${line}-${index}`}
              direction="row"
              spacing={1}
              sx={{ alignItems: "flex-start", pl: 0.5 }}
            >
              <Typography component="span" variant="body2">
                ・
              </Typography>
              <Typography
                component="span"
                variant="body2"
                sx={{ wordBreak: "break-word" }}
              >
                {line.slice(2)}
              </Typography>
            </Stack>
          );
        }

        return (
          <Typography
            key={`${line}-${index}`}
            variant="body2"
            sx={{ lineHeight: 1.8, wordBreak: "break-word" }}
          >
            {line}
          </Typography>
        );
      })}
    </Stack>
  );
}

export function ReportDetailModal({
  report,
  generatedReport,
  onClose,
}: ReportDetailModalProps) {
  const open = report !== null || generatedReport !== null;

  if (generatedReport) {
    const status = getStatusPresentation(generatedReport.report.status);
    const statistics: StatisticItem[] = [
      { label: "測定件数", value: `${generatedReport.report.record_count}件` },
      { label: "最小値", value: `${formatNumber(generatedReport.report.minimum_value)} mm/s` },
      { label: "最大値", value: `${formatNumber(generatedReport.report.maximum_value)} mm/s` },
      { label: "平均値", value: `${formatNumber(generatedReport.report.average_value)} mm/s` },
      { label: "中央値", value: `${formatNumber(generatedReport.report.median_value)} mm/s` },
      { label: "標準偏差", value: formatNumber(generatedReport.report.standard_deviation) },
      { label: "閾値", value: `${formatNumber(generatedReport.report.threshold_value)} mm/s` },
      { label: "異常件数", value: `${generatedReport.report.anomaly_count}件` },
      { label: "異常率", value: formatRate(generatedReport.analysis.anomaly_rate) },
    ];

    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>レポート詳細</DialogTitle>
        <DialogContent dividers sx={{ maxHeight: "75vh" }}>
          <Stack spacing={2.5}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={1}
              sx={{ alignItems: { xs: "flex-start", sm: "center" } }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {generatedReport.report.title}
              </Typography>
              <Chip size="small" label={status.label} color={status.color} />
            </Stack>

            <Typography variant="body2" color="text.secondary">
              設備ID: {generatedReport.report.equipment_id}
              {" / "}
              測定日: {formatNullable(generatedReport.report.measurement_date)}
              {" / "}
              天候: {formatNullable(generatedReport.report.weather)}
            </Typography>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(2, minmax(0, 1fr))",
                  md: "repeat(3, minmax(0, 1fr))",
                },
                gap: 1,
              }}
            >
              {statistics.map((item) => (
                <Box
                  key={item.label}
                  sx={{
                    p: 1.25,
                    border: 1,
                    borderColor: "divider",
                    borderRadius: 1.5,
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {item.label}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {item.value}
                  </Typography>
                </Box>
              ))}
            </Box>

            <Divider />

            <Box>
              <Typography
                variant="subtitle1"
                color="primary.dark"
                sx={{ fontWeight: 700, mb: 1 }}
              >
                AI分析
              </Typography>
              <AnalysisContent text={generatedReport.report.ai_analysis} />
            </Box>

            <Box>
              <Typography
                variant="subtitle1"
                color="primary.dark"
                sx={{ fontWeight: 700, mb: 1 }}
              >
                推奨対応
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ whiteSpace: "pre-wrap", lineHeight: 1.8 }}
              >
                {formatNullable(generatedReport.report.recommendation)}
              </Typography>
            </Box>

            {generatedReport.analysis.anomalies.length > 0 && (
              <Box>
                <Typography
                  variant="subtitle1"
                  color="primary.dark"
                  sx={{ fontWeight: 700, mb: 1 }}
                >
                  異常候補
                </Typography>
                <Stack spacing={1}>
                  {generatedReport.analysis.anomalies.map((anomaly, index) => (
                    <Box
                      key={`${anomaly.row_number}-${anomaly.measured_at}`}
                      sx={{
                        p: 1.25,
                        border: 1,
                        borderColor: "error.light",
                        borderRadius: 1.5,
                        bgcolor: "error.50",
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 700 }}>
                        異常候補 {index + 1}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        測定日時: {formatMeasuredAt(anomaly.measured_at)}
                      </Typography>
                      <Typography variant="body2">
                        値: {formatNumber(anomaly.value)} mm/s
                        {" / "}
                        閾値: {formatNumber(anomaly.threshold)} mm/s
                        {" / "}
                        超過量: {formatNumber(anomaly.excess_value)} mm/s
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <PdfDownloadButton reportId={generatedReport.report.id} />
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>レポート詳細</DialogTitle>
      <DialogContent dividers>
        {report ? (
          <Stack spacing={1}>
            <Typography variant="body1" sx={{ fontWeight: 700 }}>
              {report.period} / {report.equipmentId ?? "設備未設定"}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              使用ファイル: {report.file}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              検知結果: {report.status}（{report.anomalyCount}）
            </Typography>
          </Stack>
        ) : null}
      </DialogContent>
      <DialogActions>
        <PdfDownloadButton reportId={report?.id} />
      </DialogActions>
    </Dialog>
  );
}
