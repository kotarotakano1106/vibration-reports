export type UploadedFileResponse = {
  id: string;
  uploaded_by: string;
  equipment_id: string;
  original_filename: string;
  stored_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string | null;
  encoding: string;
  checksum: string;
  measurement_date: string | null;
  status: string;
  error_code: string | null;
  error_message: string | null;
  uploaded_at: string;
  updated_at: string;
};

export type FileUploadResponse = {
  message: string;
  is_duplicate: boolean;
  uploaded_file: UploadedFileResponse;
};

export type CsvUploadInput = {
  file: File;
  equipmentId: string;
  measurementDate: string;
  encoding: string;
};

export type CsvAnalysisStatus = "idle" | "uploading" | "generating" | "success" | "error";
