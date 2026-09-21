import {
  Chip,
  Paper,
  Stack,
  Typography,
} from "@mui/material";

import { gradientTokens } from "@/theme/tokens";

import type { ChatMessage as ChatMessageType } from "../types/chat";

type ChatMessageProps = {
  message: ChatMessageType;
};

const chunkTypeLabels: Record<string, string> = {
  analysis_summary: "分析概要",
  judgment_reason: "判定根拠",
  recommendation: "推奨対応",
  anomaly_details: "異常候補",
  full_report: "レポート全文",
};

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <Paper
      variant="outlined"
      sx={{
        alignSelf: isUser ? "flex-end" : "flex-start",
        maxWidth: "92%",
        p: 1.5,
        border: isUser ? 0 : undefined,
        color: isUser
          ? "primary.contrastText"
          : "text.primary",
        background: isUser
          ? gradientTokens.primary
          : undefined,
      }}
    >
      <Typography
        variant="body2"
        sx={{ whiteSpace: "pre-wrap" }}
      >
        {message.content}
      </Typography>

      {!isUser && message.sources?.length ? (
        <Stack spacing={0.75} sx={{ mt: 1.5 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: 700 }}
          >
            参照元
          </Typography>

          <Stack
            direction="row"
            useFlexGap
            sx={{
              flexWrap: "wrap",
              gap: 0.75,
            }}
          >
            {message.sources.map((source) => (
              <Chip
                key={source.report_chunk_id}
                size="small"
                variant="outlined"
                label={`${
                  chunkTypeLabels[source.chunk_type] ??
                  source.chunk_type
                } / ${source.equipment_id} / ${
                  source.measurement_date ?? "日付未設定"
                }`}
                title={`類似度: ${source.similarity.toFixed(3)}`}
                sx={{
                  height: 24,
                  "& .MuiChip-label": {
                    px: 1,
                    fontSize: 10.5,
                  },
                }}
              />
            ))}
          </Stack>
        </Stack>
      ) : null}
    </Paper>
  );
}
