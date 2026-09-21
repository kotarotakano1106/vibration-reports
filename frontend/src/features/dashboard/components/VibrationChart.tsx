import { useState } from "react";
import { MoreVert } from "@mui/icons-material";
import {
  Box,
  Card,
  CircularProgress,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import { colorTokens } from "@/theme/tokens";
import type {
  MeasurementDataResponse,
  MeasurementPoint,
} from "../types/measurement";

type VibrationChartProps = {
  data: MeasurementDataResponse | null;
  isLoading: boolean;
};

type ChartPoint = {
  source: MeasurementPoint;
  x: number;
  y: number;
};

const CHART_WIDTH = 800;
const CHART_HEIGHT = 190;
const PLOT_LEFT = 48;
const PLOT_RIGHT = 782;
const PLOT_TOP = 18;
const PLOT_BOTTOM = 154;
const PLOT_WIDTH = PLOT_RIGHT - PLOT_LEFT;
const PLOT_HEIGHT = PLOT_BOTTOM - PLOT_TOP;
const TOOLTIP_WIDTH = 164;
const TOOLTIP_HEIGHT = 58;
const TOOLTIP_GAP = 10;

function formatTime(value: string): string {
  return value.length >= 19 ? value.slice(11, 19) : value;
}

function formatValue(value: number): string {
  return value.toFixed(2);
}

function shouldShowTimeLabel(
  index: number,
  pointCount: number,
): boolean {
  if (pointCount <= 8) return true;

  const interval = Math.ceil((pointCount - 1) / 7);
  return (
    index === 0
    || index === pointCount - 1
    || index % interval === 0
  );
}

function calculateMaximumValue(data: MeasurementDataResponse): number {
  const maximum = Math.max(
    ...data.measurements.map((measurement) => measurement.vibration_value),
    data.threshold_value,
    1,
  );

  return maximum * 1.15;
}

function createChartPoints(
  data: MeasurementDataResponse,
  maximumValue: number,
): ChartPoint[] {
  const denominator = Math.max(data.measurements.length - 1, 1);

  return data.measurements.map((measurement, index) => ({
    source: measurement,
    x: PLOT_LEFT + (index / denominator) * PLOT_WIDTH,
    y:
      PLOT_BOTTOM
      - (measurement.vibration_value / maximumValue) * PLOT_HEIGHT,
  }));
}

function createPolylinePoints(points: ChartPoint[]): string {
  return points
    .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(" ");
}

export function VibrationChart({
  data,
  isLoading,
}: VibrationChartProps) {
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(
    null,
  );
  let chartContent;

  if (isLoading) {
    chartContent = (
      <Stack
        spacing={1}
        sx={{
          height: "100%",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress size={24} />
        <Typography variant="caption" color="text.secondary">
          測定データを取得しています...
        </Typography>
      </Stack>
    );
  } else if (!data || data.measurements.length === 0) {
    chartContent = (
      <Stack
        sx={{
          height: "100%",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography variant="body2" color="text.secondary">
          CSVをアップロードすると振動推移が表示されます。
        </Typography>
      </Stack>
    );
  } else {
    const maximumValue = calculateMaximumValue(data);
    const chartPoints = createChartPoints(data, maximumValue);
    const polylinePoints = createPolylinePoints(chartPoints);
    const thresholdY =
      PLOT_BOTTOM
      - (data.threshold_value / maximumValue) * PLOT_HEIGHT;
    const gridLineCount = 4;

    chartContent = (
      <>
        <Stack
          direction="row"
          spacing={2}
          sx={{ mb: 0.5, flexWrap: "wrap" }}
        >
          <Typography
            variant="caption"
            sx={{ color: colorTokens.chart.vibration }}
          >
            ━ 振動値
          </Typography>
          <Typography variant="caption" color="error.main">
            ━ 異常判定閾値（{formatValue(data.threshold_value)}）
          </Typography>
          <Typography variant="caption" color="text.secondary">
            設備ID: {data.equipment_id}
          </Typography>
        </Stack>

        <svg
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
          width="100%"
          height="calc(100% - 20px)"
          role="img"
          aria-label={`${data.equipment_id}の振動推移`}
        >
          {Array.from({ length: gridLineCount + 1 }, (_, index) => {
            const ratio = index / gridLineCount;
            const y = PLOT_TOP + ratio * PLOT_HEIGHT;
            const value = maximumValue * (1 - ratio);

            return (
              <g key={y}>
                <line
                  x1={PLOT_LEFT}
                  x2={PLOT_RIGHT}
                  y1={y}
                  y2={y}
                  stroke={colorTokens.surface.border}
                />
                <text
                  x="4"
                  y={y + 3}
                  fill={colorTokens.text.secondary}
                  fontSize="9"
                >
                  {formatValue(value)}
                </text>
              </g>
            );
          })}

          <line
            x1={PLOT_LEFT}
            x2={PLOT_RIGHT}
            y1={thresholdY}
            y2={thresholdY}
            stroke={colorTokens.status.error}
            strokeWidth="1.5"
            strokeDasharray="6 4"
          />

          <polyline
            points={polylinePoints}
            fill="none"
            stroke={colorTokens.chart.vibration}
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {chartPoints.map((point, index) => {
            const fillColor = point.source.is_anomaly
              ? colorTokens.status.error
              : colorTokens.chart.vibration;

            return (
              <g
                key={`${point.source.measured_at}-${index}`}
                tabIndex={0}
                role="button"
                aria-label={`${formatTime(
                  point.source.measured_at,
                )}、振動値 ${formatValue(
                  point.source.vibration_value,
                )} mm/s${point.source.is_anomaly ? "、異常" : "、正常"}`}
                onMouseEnter={() => setHoveredPointIndex(index)}
                onMouseLeave={() => setHoveredPointIndex(null)}
                onFocus={() => setHoveredPointIndex(index)}
                onBlur={() => setHoveredPointIndex(null)}
              >
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={
                    hoveredPointIndex === index
                      ? point.source.is_anomaly ? 7 : 6
                      : point.source.is_anomaly ? 5 : 3.5
                  }
                  fill={fillColor}
                  stroke={
                    point.source.is_anomaly
                      ? colorTokens.surface.paper
                      : "none"
                  }
                  strokeWidth="2"
                >
                  <title>
                    {formatTime(point.source.measured_at)} / {formatValue(
                      point.source.vibration_value,
                    )}
                    {point.source.is_anomaly ? " / 異常" : ""}
                  </title>
                </circle>
                {shouldShowTimeLabel(
                  index,
                  chartPoints.length,
                ) && (
                  <text
                    x={point.x}
                    y={178}
                    textAnchor={
                      index === 0
                        ? "start"
                        : index === chartPoints.length - 1
                          ? "end"
                          : "middle"
                    }
                    fill={colorTokens.text.secondary}
                    fontSize="9"
                  >
                    {formatTime(point.source.measured_at)}
                  </text>
                )}
              </g>
            );
          })}

          {hoveredPointIndex !== null && (() => {
            const hoveredPoint = chartPoints[hoveredPointIndex];
            const tooltipX = Math.min(
              Math.max(
                hoveredPoint.x - TOOLTIP_WIDTH / 2,
                PLOT_LEFT,
              ),
              PLOT_RIGHT - TOOLTIP_WIDTH,
            );
            const showBelow = (
              hoveredPoint.y - TOOLTIP_HEIGHT - TOOLTIP_GAP
              < PLOT_TOP
            );
            const tooltipY = showBelow
              ? hoveredPoint.y + TOOLTIP_GAP
              : hoveredPoint.y - TOOLTIP_HEIGHT - TOOLTIP_GAP;

            return (
              <g pointerEvents="none">
                <rect
                  x={tooltipX}
                  y={tooltipY}
                  width={TOOLTIP_WIDTH}
                  height={TOOLTIP_HEIGHT}
                  rx="6"
                  fill={colorTokens.surface.paper}
                  stroke={colorTokens.surface.border}
                  strokeWidth="1"
                />
                <text
                  x={tooltipX + 10}
                  y={tooltipY + 18}
                  fill={colorTokens.text.primary}
                  fontSize="11"
                  fontWeight="700"
                >
                  測定時刻: {formatTime(
                    hoveredPoint.source.measured_at,
                  )}
                </text>
                <text
                  x={tooltipX + 10}
                  y={tooltipY + 35}
                  fill={colorTokens.text.secondary}
                  fontSize="10"
                >
                  振動値: {formatValue(
                    hoveredPoint.source.vibration_value,
                  )} mm/s
                </text>
                <text
                  x={tooltipX + 10}
                  y={tooltipY + 50}
                  fill={
                    hoveredPoint.source.is_anomaly
                      ? colorTokens.status.error
                      : colorTokens.chart.vibration
                  }
                  fontSize="10"
                  fontWeight="700"
                >
                  判定: {
                    hoveredPoint.source.is_anomaly ? "異常" : "正常"
                  }
                </text>
              </g>
            );
          })()}
        </svg>
      </>
    );
  }

  return (
    <Card sx={{ height: "100%" }}>
      <Stack
        direction="row"
        sx={{
          height: 50,
          px: 2,
          borderBottom: 1,
          borderColor: "divider",
          alignItems: "center",
        }}
      >
        <Typography variant="subtitle1" color="primary.dark">
          振動推移
        </Typography>
        <Box sx={{ flex: 1 }} />
        <IconButton size="small" aria-label="グラフ操作">
          <MoreVert fontSize="small" />
        </IconButton>
      </Stack>

      <Box
        sx={{
          px: 2,
          pt: 1.5,
          height: "calc(100% - 50px)",
          minHeight: 0,
        }}
      >
        {chartContent}
      </Box>
    </Card>
  );
}
