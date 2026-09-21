"use client";

import { useState } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import type { ReportGenerationResponse } from "@/features/reports/types/report";

import { useCsvAnalysis } from "../hooks/useCsvAnalysis";
import { AnalysisProgress } from "./AnalysisProgress";
import { CsvDropzone } from "./CsvDropzone";
import { CsvFilePreview } from "./CsvFilePreview";

type CsvUploadModalProps = {
  open: boolean;
  onClose: () => void;
  onCompleted: (result: ReportGenerationResponse) => void;
};

const defaultEquipmentId = "";
const defaultMeasurementDate = "";
const defaultEncoding = "UTF-8";
const defaultThresholdValue = 2;
const defaultWeather = "";

export function CsvUploadModal({
  open,
  onClose,
  onCompleted,
}: CsvUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [equipmentId, setEquipmentId] = useState(
    defaultEquipmentId,
  );
  const [measurementDate, setMeasurementDate] = useState(
    defaultMeasurementDate,
  );
  const [encoding, setEncoding] = useState(defaultEncoding);
  const [thresholdValue, setThresholdValue] = useState(
    defaultThresholdValue,
  );
  const [weather, setWeather] = useState(defaultWeather);
  const [showValidation, setShowValidation] = useState(false);

  const {
    error,
    isPending,
    progressMessage,
    execute,
    reset,
  } = useCsvAnalysis();

  const normalizedEquipmentId = equipmentId.trim();
  const normalizedMeasurementDate = measurementDate.trim();
  const normalizedEncoding = encoding.trim();
  const normalizedWeather = weather.trim();

  const equipmentIdError =
    showValidation && !normalizedEquipmentId;
  const measurementDateError =
    showValidation && !normalizedMeasurementDate;
  const encodingError = showValidation && !normalizedEncoding;
  const thresholdError =
    showValidation &&
    (!Number.isFinite(thresholdValue) || thresholdValue <= 0);

  const isFormValid = Boolean(
    file &&
      normalizedEquipmentId &&
      normalizedMeasurementDate &&
      normalizedEncoding &&
      Number.isFinite(thresholdValue) &&
      thresholdValue > 0,
  );

  const resetForm = () => {
    setFile(null);
    setEquipmentId(defaultEquipmentId);
    setMeasurementDate(defaultMeasurementDate);
    setEncoding(defaultEncoding);
    setThresholdValue(defaultThresholdValue);
    setWeather(defaultWeather);
    setShowValidation(false);
    reset();
  };

  const close = () => {
    if (isPending) {
      return;
    }

    resetForm();
    onClose();
  };

  const handleThresholdChange = (value: string) => {
    const parsed = Number(value);
    setThresholdValue(Number.isNaN(parsed) ? 0 : parsed);
  };

  const handleExecute = async () => {
    setShowValidation(true);

    if (!isFormValid || !file || isPending) {
      return;
    }

    const completedResult = await execute({
      file,
      equipmentId: normalizedEquipmentId,
      measurementDate: normalizedMeasurementDate,
      encoding: normalizedEncoding,
      thresholdValue,
      weather: normalizedWeather,
    });

    if (!completedResult) {
      return;
    }

    onCompleted(completedResult);
    resetForm();
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>CSVアップロード</DialogTitle>

      <DialogContent>
        <CsvDropzone
          onSelect={(selectedFile) => {
            setFile(selectedFile);
            setShowValidation(false);
          }}
        />

        {file && <CsvFilePreview file={file} />}

        <Stack spacing={2} sx={{ mt: 2 }}>
          <TextField
            required
            label="設備ID"
            value={equipmentId}
            onChange={(event) =>
              setEquipmentId(event.target.value)
            }
            disabled={isPending}
            error={equipmentIdError}
            helperText={
              equipmentIdError
                ? "設備IDを入力してください。"
                : "例: MOTOR-TEST-002"
            }
            size="small"
            autoComplete="off"
          />

          <TextField
            required
            label="測定日"
            type="date"
            value={measurementDate}
            onChange={(event) =>
              setMeasurementDate(event.target.value)
            }
            disabled={isPending}
            error={measurementDateError}
            helperText={
              measurementDateError
                ? "測定日を入力してください。"
                : "CSVデータの測定対象日を指定してください。"
            }
            size="small"
            slotProps={{
              inputLabel: { shrink: true },
            }}
          />

          <TextField
            required
            label="文字コード"
            value={encoding}
            onChange={(event) =>
              setEncoding(event.target.value)
            }
            disabled={isPending}
            error={encodingError}
            helperText={
              encodingError
                ? "文字コードを入力してください。"
                : "通常はUTF-8を使用します。"
            }
            size="small"
          />

          <TextField
            required
            label="異常判定の閾値"
            type="number"
            value={thresholdValue}
            onChange={(event) =>
              handleThresholdChange(event.target.value)
            }
            disabled={isPending}
            error={thresholdError}
            helperText={
              thresholdError
                ? "0より大きい閾値を入力してください。"
                : "単位: mm/s"
            }
            size="small"
            slotProps={{
              htmlInput: {
                step: 0.1,
                min: 0.1,
              },
            }}
          />

          <TextField
            label="天候（任意）"
            value={weather}
            onChange={(event) =>
              setWeather(event.target.value)
            }
            disabled={isPending}
            size="small"
          />
        </Stack>

        {isPending && progressMessage && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mt: 2 }}
          >
            {progressMessage}
          </Typography>
        )}

        <AnalysisProgress active={isPending} />

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error.message}
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={close} disabled={isPending}>
          キャンセル
        </Button>

        <Button
          variant="contained"
          disabled={!isFormValid || isPending}
          onClick={handleExecute}
        >
          アップロードして分析
        </Button>
      </DialogActions>
    </Dialog>
  );
}
