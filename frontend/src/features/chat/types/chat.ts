export type RagChatSource = {
  report_chunk_id: string;
  report_id: string;
  chunk_type: string;
  equipment_id: string;
  measurement_date: string | null;
  similarity: number;
};

export type RagChatRequest = {
  query: string;
  limit?: number;
  equipment_id?: string | null;
  measurement_date_from?: string | null;
  measurement_date_to?: string | null;
  chunk_types?: string[];
};

export type RagChatResponse = {
  query: string;
  answer: string;
  source_count: number;
  sources: RagChatSource[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: RagChatSource[];
};
