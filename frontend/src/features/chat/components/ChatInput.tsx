"use client";

import { useState } from "react";
import { Send } from "@mui/icons-material";
import {
  CircularProgress,
  IconButton,
  Stack,
  TextField,
} from "@mui/material";

import { gradientTokens } from "@/theme/tokens";

type ChatInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
};

export function ChatInput({
  onSend,
  disabled = false,
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  const submit = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) {
      return;
    }

    onSend(trimmed);
    setMessage("");
  };

  return (
    <Stack
      component="form"
      direction="row"
      spacing={1}
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
      sx={{
        p: 2,
        borderTop: 1,
        borderColor: "divider",
      }}
    >
      <TextField
        fullWidth
        size="small"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="質問を入力してください..."
        slotProps={{
        htmlInput: {
          "aria-label": "AIへの質問",
        },
      }}
        disabled={disabled}
      />

      <IconButton
        type="submit"
        aria-label="質問を送信"
        disabled={disabled || !message.trim()}
        sx={{
          background: gradientTokens.primary,
          color: "primary.contrastText",
          "&.Mui-disabled": {
            color: "action.disabled",
            background: "action.disabledBackground",
          },
        }}
      >
        {disabled ? (
          <CircularProgress size={18} color="inherit" />
        ) : (
          <Send fontSize="small" />
        )}
      </IconButton>
    </Stack>
  );
}

