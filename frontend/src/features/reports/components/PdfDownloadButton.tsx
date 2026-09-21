"use client";

import { useState } from "react";
import { PictureAsPdfOutlined } from "@mui/icons-material";
import {
  Button,
  CircularProgress,
  Tooltip,
} from "@mui/material";

import { downloadReportPdf } from "../api/download-report-pdf";

type PdfDownloadButtonProps = {
  reportId?: string | null;
};

export function PdfDownloadButton({
  reportId,
}: PdfDownloadButtonProps) {
  const [isPending, setIsPending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDownload = async () => {
    if (!reportId || isPending) return;

    setIsPending(true);
    setErrorMessage(null);
    try {
      await downloadReportPdf(reportId);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "PDFのダウンロードに失敗しました。",
      );
    } finally {
      setIsPending(false);
    }
  };

  const title = !reportId
    ? "保存済みのAIレポートからPDFを出力できます"
    : errorMessage ?? "PDFをダウンロード";

  return (
    <Tooltip title={title}>
      <span>
        <Button
          variant="outlined"
          startIcon={
            isPending ? (
              <CircularProgress size={16} />
            ) : (
              <PictureAsPdfOutlined />
            )
          }
          disabled={!reportId || isPending}
          onClick={() => void handleDownload()}
        >
          {isPending ? "PDF生成中..." : "PDF出力"}
        </Button>
      </span>
    </Tooltip>
  );
}
