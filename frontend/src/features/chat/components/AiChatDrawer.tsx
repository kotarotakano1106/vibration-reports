"use client";

import { useState } from "react";
import { Close } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Drawer,
  IconButton,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { alpha } from "@mui/material/styles";

import { colorTokens, layoutTokens } from "@/theme/tokens";

import { useRagChat } from "../hooks/useRagChat";
import type { ChatMessage } from "../types/chat";
import { ChatInput } from "./ChatInput";
import { ChatMessageList } from "./ChatMessageList";

type AiChatDrawerProps = {
  open: boolean;
  onClose: () => void;
  equipmentId?: string | null;
  measurementDate?: string | null;
};

const quickQuestions = [
  "異常の原因を教えて",
  "推奨対応を教えて",
  "前月との比較を教えて",
  "点検の優先順位を教えて",
];

function toMonthRange(value?: string | null): {
  from: string | null;
  to: string | null;
  label: string;
} {
  if (!value) return { from: null, to: null, label: "指定なし" };

  const normalized = value.slice(0, 10);
  const [year, month] = normalized.split("-").map(Number);
  const endDay = new Date(year, month, 0).getDate();

  return {
    from: `${year}-${String(month).padStart(2, "0")}-01`,
    to: `${year}-${String(month).padStart(2, "0")}-${String(endDay).padStart(2, "0")}`,
    label: `${year}年${month}月`,
  };
}

export function AiChatDrawer({
  open,
  onClose,
  equipmentId,
  measurementDate,
}: AiChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { error, isPending, send } = useRagChat();
  const period = toMonthRange(measurementDate);

  const handleSend = async (content: string) => {
    if (isPending) return;

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content },
    ]);

    const response = await send({
      query: content,
      limit: 4,
      equipment_id: equipmentId ?? null,
      measurement_date_from: period.from,
      measurement_date_to: period.to,
      chunk_types: [
        "analysis_summary",
        "judgment_reason",
        "recommendation",
        "anomaly_details",
      ],
    });

    if (!response) return;

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      },
    ]);
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      hideBackdrop
      slotProps={{
        paper: {
          sx: {
            top: layoutTokens.headerHeight,
            height: `calc(100% - ${layoutTokens.headerHeight}px)`,
            width: layoutTokens.aiDrawerWidth,
            borderLeft: 1,
            borderColor: "divider",
            boxShadow: "none",
          },
        },
      }}
    >
      <Stack sx={{ height: "100%" }}>
        <Stack direction="row" sx={{ minHeight: 62, px: 2, alignItems: "center" }}>
          <Typography variant="h6">AIアシスタント</Typography>
          <Box sx={{ flex: 1 }} />
          <IconButton aria-label="AI相談を閉じる" onClick={onClose}>
            <Close />
          </IconButton>
        </Stack>

        <Box sx={{ px: 2 }}>
          <Typography variant="caption" sx={{ fontWeight: 700 }}>
            参照中の情報
          </Typography>
          <Paper variant="outlined" sx={{ mt: 0.75, p: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              振動モニタリング
            </Typography>
            <Typography variant="caption" component="div" sx={{ mt: 1 }}>
              設備ID：{equipmentId ?? "指定なし"}
            </Typography>
            <Typography variant="caption" component="div">
              期間：{period.label}
            </Typography>
          </Paper>

          <Typography variant="caption" component="div" sx={{ mt: 2, mb: 0.75, fontWeight: 700 }}>
            よくある質問
          </Typography>
          <Stack spacing={0.75}>
            {quickQuestions.map((text) => (
              <Button
                key={text}
                variant="outlined"
                size="small"
                disabled={isPending}
                onClick={() => void handleSend(text)}
                sx={{
                  justifyContent: "flex-start",
                  color: "text.primary",
                  borderColor: alpha(colorTokens.brand.primary, 0.28),
                }}
              >
                {text}
              </Button>
            ))}
          </Stack>
        </Box>

        {error ? (
          <Alert severity="error" sx={{ mx: 2, mt: 1.5 }}>
            {error.message}
          </Alert>
        ) : null}

        <ChatMessageList messages={messages} isPending={isPending} />
        <ChatInput onSend={(content) => void handleSend(content)} disabled={isPending} />
      </Stack>
    </Drawer>
  );
}
