export type MeasurementPoint = {
  measured_at: string;
  vibration_value: number;
  is_anomaly: boolean;
};

export type MeasurementDataResponse = {
  uploaded_file_id: string;
  equipment_id: string;
  measurement_date: string | null;
  measurement_count: number;
  threshold_value: number;
  measurements: MeasurementPoint[];
};

export type GetMeasurementsInput = {
  uploadedFileId: string;
  thresholdValue: number;
};