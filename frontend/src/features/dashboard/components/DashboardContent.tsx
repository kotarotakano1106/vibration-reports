"use client";

import { Alert, Box } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppHeader } from "@/components/layout/AppHeader";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { CsvUploadModal } from "@/features/analysis/components/CsvUploadModal";
import { AiChatDrawer } from "@/features/chat/components/AiChatDrawer";
import { getReports } from "@/features/reports/api/get-reports";
import { ReportDetailModal } from "@/features/reports/components/ReportDetailModal";
import { ReportList } from "@/features/reports/components/ReportList";
import type {
  Report,
  ReportGenerationResponse,
  ReportListItemResponse,
  ReportStatus,
  VibrationAnalysisResponse,
} from "@/features/reports/types/report";
import { layoutTokens } from "@/theme/tokens";

import { useMeasurements } from "../hooks/useMeasurements";
import type { MeasurementDataResponse } from "../types/measurement";
import { DashboardHeader } from "./DashboardHeader";
import { MonitoringSummary } from "./MonitoringSummary";
import { VibrationChart } from "./VibrationChart";

function toDisplayStatus(status: string): ReportStatus {
  if (status === "normal") return "正常";
  if (status === "requires_attention") return "異常";
  return "注意";
}

function formatDate(value: string): string {
  return value.slice(0, 10).replaceAll("-", "/");
}

function formatPeriod(value: string | null): string {
  if (!value) return "測定日未設定";
  const [year, month] = value.split("-");
  return `${year}年${Number(month)}月`;
}

function toReport(item: ReportListItemResponse): Report {
  return {
    id: item.id,
    uploadedFileId: item.uploaded_file_id,
    thresholdValue: item.threshold_value,
    date: formatDate(item.created_at),
    period: formatPeriod(item.measurement_date),
    file: item.original_filename,
    status: toDisplayStatus(item.status),
    anomalyCount: `${item.anomaly_count}件`,
    equipmentId: item.equipment_id,
    createdBy: "開発ユーザー",
  };
}

function toGeneratedReport(result: ReportGenerationResponse): Report {
  return {
    id: result.report.id,
    uploadedFileId: result.report.uploaded_file_id,
    thresholdValue:
      result.report.threshold_value ?? result.analysis.threshold_value,
    date: formatDate(result.report.created_at),
    period: formatPeriod(result.report.measurement_date),
    file: "アップロード済みCSV",
    status: toDisplayStatus(result.report.status),
    anomalyCount: `${result.analysis.anomaly_count}件`,
    equipmentId: result.report.equipment_id,
    createdBy: "開発ユーザー",
    generatedReport: result,
  };
}

function toAnalysis(data: MeasurementDataResponse): VibrationAnalysisResponse {
  const values = data.measurements.map((item) => item.vibration_value);
  const anomalies = data.measurements
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => item.is_anomaly)
    .map(({ item, index }) => ({
      row_number: index + 1,
      measured_at: item.measured_at,
      value: item.vibration_value,
      threshold: data.threshold_value,
      excess_value: Math.max(
        item.vibration_value - data.threshold_value,
        0,
      ),
    }));
  const count = values.length;
  const average = count
    ? values.reduce((sum, value) => sum + value, 0) / count
    : 0;
  const sorted = [...values].sort((a, b) => a - b);
  const median =
    count === 0
      ? 0
      : count % 2
        ? sorted[Math.floor(count / 2)]
        : (sorted[count / 2 - 1] + sorted[count / 2]) / 2;
  const variance = count
    ? values.reduce((sum, value) => sum + (value - average) ** 2, 0) /
      count
    : 0;

  return {
    record_count: count,
    minimum_value: count ? Math.min(...values) : 0,
    maximum_value: count ? Math.max(...values) : 0,
    average_value: average,
    median_value: median,
    standard_deviation: Math.sqrt(variance),
    threshold_value: data.threshold_value,
    anomaly_count: anomalies.length,
    anomaly_rate: count ? anomalies.length / count : 0,
    status: anomalies.length ? "requires_attention" : "normal",
    anomalies,
  };
}

export function DashboardContent() {
  const [chatOpen, setChatOpen] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [reports, setReports] = useState<Report[]>([]);
  const [reportListError, setReportListError] = useState<Error | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedEquipmentId, setSelectedEquipmentId] = useState("");
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const activeId = useRef<string | null>(null);
  const [activeReport, setActiveReport] = useState<Report | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [generatedReport, setGeneratedReport] =
    useState<ReportGenerationResponse | null>(null);
  const [latestAnalysis, setLatestAnalysis] =
    useState<VibrationAnalysisResponse | null>(null);

  const {
    data: measurementData,
    error: measurementError,
    isLoading: isMeasurementsLoading,
    load: loadMeasurements,
    reset: resetMeasurements,
  } = useMeasurements();

  const equipmentIds = useMemo(
    () =>
      Array.from(
        new Set(
          reports
            .map((report) => report.equipmentId)
            .filter((value): value is string => Boolean(value)),
        ),
      ),
    [reports],
  );

  const periods = useMemo(
    () =>
      Array.from(
        new Set(
          reports
            .filter(
              (report) => report.equipmentId === selectedEquipmentId,
            )
            .map((report) => report.period),
        ),
      ),
    [reports, selectedEquipmentId],
  );

  const displayReport = useCallback(
    async (report: Report | null) => {
      activeId.current = report?.id ?? null;
      setActiveReport(report);

      if (!report) {
        setLatestAnalysis(null);
        resetMeasurements();
        return;
      }

      if (report.generatedReport) {
        setLatestAnalysis(report.generatedReport.analysis);
      }

      const response = await loadMeasurements({
        uploadedFileId: report.uploadedFileId,
        thresholdValue: report.thresholdValue ?? 2,
      });

      if (response) {
        setLatestAnalysis(toAnalysis(response));
      }
    },
    [loadMeasurements, resetMeasurements],
  );

  const loadReports = useCallback(
    async (preferredId?: string) => {
      setIsRefreshing(true);
      try {
        const items = await getReports();
        const next = items.map(toReport);
        setReports(next);
        setReportListError(null);

        const report =
          next.find((item) => item.id === preferredId) ??
          next.find((item) => item.id === activeId.current) ??
          next[0] ??
          null;

        setSelectedEquipmentId(report?.equipmentId ?? "");
        setSelectedPeriod(report?.period ?? "");
        await displayReport(report);
      } catch (error) {
        setReportListError(
          error instanceof Error
            ? error
            : new Error("レポート一覧を取得できませんでした。"),
        );
      } finally {
        setIsRefreshing(false);
      }
    },
    [displayReport],
  );

  useEffect(() => {
    const initialize = async () => {
      await Promise.resolve();
      await loadReports();
    };

    void initialize();
  }, [loadReports]);

  const changeEquipment = useCallback(
    (value: string) => {
      setSelectedEquipmentId(value);
      const report =
        reports.find((item) => item.equipmentId === value) ?? null;
      setSelectedPeriod(report?.period ?? "");
      void displayReport(report);
    },
    [displayReport, reports],
  );

  const changePeriod = useCallback(
    (value: string) => {
      setSelectedPeriod(value);
      const report =
        reports.find(
          (item) =>
            item.equipmentId === selectedEquipmentId &&
            item.period === value,
        ) ?? null;
      void displayReport(report);
    },
    [displayReport, reports, selectedEquipmentId],
  );

  const uploadCompleted = useCallback(
    (result: ReportGenerationResponse) => {
      const report = toGeneratedReport(result);
      setReports((current) => [
        report,
        ...current.filter((item) => item.id !== report.id),
      ]);
      setGeneratedReport(result);
      setSelectedReport(null);
      setSelectedEquipmentId(report.equipmentId ?? "");
      setSelectedPeriod(report.period);
      setUploadOpen(false);
      void displayReport(report);
      void loadReports(report.id);
    },
    [displayReport, loadReports],
  );

  const selectReport = useCallback((report: Report) => {
    if (report.generatedReport) {
      setSelectedReport(null);
      setGeneratedReport(report.generatedReport);
    } else {
      setGeneratedReport(null);
      setSelectedReport(report);
    }
  }, []);

  const closeDetail = useCallback(() => {
    setSelectedReport(null);
    setGeneratedReport(null);
  }, []);

  return (
    <Box
      sx={{
        height: "100dvh",
        bgcolor: "background.default",
        overflow: "hidden",
      }}
    >
      <AppHeader onOpenChat={() => setChatOpen(true)} />
      <AppSidebar />
      <Box
        component="main"
        sx={{
          position: "fixed",
          top: layoutTokens.headerHeight,
          bottom: 0,
          left: layoutTokens.navigationWidth,
          right: chatOpen ? layoutTokens.aiDrawerWidth : 0,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            height: "100%",
            p: "13px 24px 18px",
            display: "grid",
            gridTemplateRows: "30px minmax(190px, 31vh) minmax(0, 1fr)",
            gap: 1.5,
          }}
        >
          <DashboardHeader
            equipmentIds={equipmentIds}
            periods={periods}
            selectedEquipmentId={selectedEquipmentId}
            selectedPeriod={selectedPeriod}
            isRefreshing={isRefreshing}
            onEquipmentChange={changeEquipment}
            onPeriodChange={changePeriod}
            onRefresh={() => void loadReports()}
            onOpenUpload={() => setUploadOpen(true)}
          />
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: ".72fr 1.28fr",
              gap: 1.5,
              minHeight: 0,
            }}
          >
            <MonitoringSummary analysis={latestAnalysis} />
            <VibrationChart
              data={measurementData}
              isLoading={isMeasurementsLoading}
            />
          </Box>
          <ReportList reports={reports} onSelect={selectReport} />
        </Box>
      </Box>

      {reportListError && (
        <Alert
          severity="error"
          sx={{
            position: "fixed",
            left: layoutTokens.navigationWidth + 24,
            bottom: 24,
            zIndex: 1500,
          }}
        >
          {reportListError.message}
        </Alert>
      )}

      {measurementError && (
        <Alert
          severity="error"
          sx={{ position: "fixed", right: 24, bottom: 24, zIndex: 1500 }}
        >
          {measurementError.message}
        </Alert>
      )}

      <CsvUploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onCompleted={uploadCompleted}
      />
      <ReportDetailModal
        report={selectedReport}
        generatedReport={generatedReport}
        onClose={closeDetail}
      />
      <AiChatDrawer
        key={[
          activeReport?.equipmentId ?? "none",
          activeReport?.period ?? "none",
        ].join(":")}
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        equipmentId={activeReport?.equipmentId ?? null}
        measurementDate={measurementData?.measurement_date ?? null}
      />
    </Box>
  );
}
