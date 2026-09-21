import { WarningAmberOutlined } from "@mui/icons-material";
import {
  alpha,
  Box,
  Card,
  Stack,
  Typography,
} from "@mui/material";

import type { VibrationAnalysisResponse } from "@/features/reports/types/report";


type MonitoringSummaryProps = {
  analysis: VibrationAnalysisResponse | null;
};


type SummaryColor = "error" | "primary" | "success";


type SummaryItem = {
  label: string;
  note: string;
  value: string;
  unit: string;
  color: SummaryColor;
};


function formatValue(value: number): string {
  return value.toFixed(2);
}


function createSummaryItems(
  analysis: VibrationAnalysisResponse | null,
): SummaryItem[] {
  if (!analysis) {
    return [
      {
        label: "異常検知件数",
        note: "CSV分析後に更新されます",
        value: "-",
        unit: "件",
        color: "error",
      },
      {
        label: "測定件数",
        note: "CSV分析後に更新されます",
        value: "-",
        unit: "件",
        color: "primary",
      },
      {
        label: "最大振動値",
        note: "CSV分析後に更新されます",
        value: "-",
        unit: "mm/s",
        color: "success",
      },
    ];
  }

  return [
    {
      label: "異常検知件数",
      note:
        analysis.anomaly_count > 0
          ? `異常率 ${(analysis.anomaly_rate * 100).toFixed(1)}%`
          : "閾値超過なし",
      value: String(analysis.anomaly_count),
      unit: "件",
      color: "error",
    },
    {
      label: "測定件数",
      note: `判定: ${analysis.status}`,
      value: String(analysis.record_count),
      unit: "件",
      color: "primary",
    },
    {
      label: "最大振動値",
      note: `閾値 ${formatValue(analysis.threshold_value)} mm/s`,
      value: formatValue(analysis.maximum_value),
      unit: "mm/s",
      color: "success",
    },
  ];
}


export function MonitoringSummary({
  analysis,
}: MonitoringSummaryProps) {
  const summaryItems = createSummaryItems(analysis);

  return (
    <Card sx={{ height: "100%" }}>
      <Box
        sx={{
          height: 50,
          px: 2,
          display: "flex",
          alignItems: "center",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Typography variant="subtitle1" color="primary.dark">
          検知サマリー
        </Typography>
      </Box>

      <Stack sx={{ height: "calc(100% - 50px)" }}>
        {summaryItems.map((item, index) => (
          <Stack
            key={item.label}
            direction="row"
            sx={{
              flex: 1,
              px: 2,
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom:
                index < summaryItems.length - 1 ? 1 : 0,
              borderColor: "divider",
            }}
          >
            <Stack
              direction="row"
              spacing={1.5}
              sx={{ alignItems: "center" }}
            >
              <Box
                sx={(theme) => ({
                  width: 42,
                  height: 42,
                  borderRadius: "50%",
                  display: "grid",
                  placeItems: "center",
                  bgcolor: alpha(theme.palette[item.color].main, 0.1),
                })}
              >
                <WarningAmberOutlined
                  color={item.color}
                  fontSize="small"
                />
              </Box>

              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {item.label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {item.note}
                </Typography>
              </Box>
            </Stack>

            <Typography
              sx={(theme) => ({
                fontSize: 18,
                fontWeight: 700,
                color: theme.palette[item.color].main,
              })}
            >
              {item.value}
              <Box component="span" sx={{ fontSize: 10, ml: 0.5 }}>
                {item.unit}
              </Box>
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Card>
  );
}
