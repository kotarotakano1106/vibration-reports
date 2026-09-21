export type ReportStatus =
  | "異常"
  | "注意"
  | "正常";

export type Report = {
  id: string;
  uploadedFileId: string;
  thresholdValue?: number | null;
  date: string;
  period: string;
  file: string;
  status: ReportStatus;
  anomalyCount: string;
  equipmentId?: string;
  createdBy?: string;
  generatedReport?: ReportGenerationResponse;
};

export type VibrationAnomalyResponse = {
  row_number: number;
  measured_at: string;
  value: number;
  threshold: number;
  excess_value: number;
};

export type VibrationAnalysisResponse = {
  record_count: number;
  minimum_value: number;
  maximum_value: number;
  average_value: number;
  median_value: number;
  standard_deviation: number;
  threshold_value: number;
  anomaly_count: number;
  anomaly_rate: number;
  status: string;
  anomalies: VibrationAnomalyResponse[];
};

export type ReportResponse = {
  id: string;
  uploaded_file_id: string;
  created_by: string;
  equipment_id: string;
  measurement_date: string | null;
  weather: string | null;
  title: string;
  record_count: number;
  minimum_value: number;
  maximum_value: number;
  average_value: number;
  median_value: number | null;
  standard_deviation: number | null;
  threshold_value: number | null;
  anomaly_count: number;
  anomaly_details: Record<string, unknown>[];
  status: string;
  ai_summary: string;
  ai_analysis: string;
  recommendation: string | null;
  report_text: string;
  ai_model: string | null;
  prompt_version: string | null;
  chart_path: string | null;
  pdf_path: string | null;
  pdf_generated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ReportListItemResponse = {
  id: string;
  uploaded_file_id: string;
  equipment_id: string;
  measurement_date: string | null;
  title: string;
  anomaly_count: number;
  status: string;
  created_by: string;
  created_at: string;
  original_filename: string;
  threshold_value: number | null;
};


export type ReportGenerationResponse = {
  message: string;
  report: ReportResponse;
  analysis: VibrationAnalysisResponse;
  report_chunk_id: string;
  embedding_model: string;
  embedding_dimensions: number;
};

export type ReportGenerateInput = {
  uploadedFileId: string;
  thresholdValue: number;
  weather: string | null;
};