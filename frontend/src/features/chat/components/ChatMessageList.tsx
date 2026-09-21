import {
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

import type { ChatMessage as ChatMessageType } from "../types/chat";
import { ChatMessage } from "./ChatMessage";

type ChatMessageListProps = {
  messages: ChatMessageType[];
  isPending?: boolean;
};

export function ChatMessageList({
  messages,
  isPending = false,
}: ChatMessageListProps) {
  return (
    <Stack
      spacing={1.5}
      sx={{
        flex: 1,
        px: 2,
        pt: 2,
        pb: 1,
        overflowY: "auto",
      }}
    >
      {messages.length === 0 && !isPending ? (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ textAlign: "center", mt: 2 }}
        >
          過去レポートについて質問してください。
        </Typography>
      ) : null}

      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {isPending ? (
        <Stack
          direction="row"
          spacing={1}
          sx={{
            alignItems: "center",
            color: "text.secondary",
          }}
        >
          <CircularProgress size={16} />
          <Typography variant="caption">
            過去レポートを検索し、回答を作成しています...
          </Typography>
        </Stack>
      ) : null}
    </Stack>
  );
}
