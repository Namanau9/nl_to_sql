export interface QueryResultData {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_ms: number;
}

export interface QueryResponse {
  question: string;
  sql: string;
  explanation: string;
  results: QueryResultData | null;
  status: "success" | "error";
  error: string | null;
  execution_ms: number;
}

export interface HealthResponse {
  status: string;
  schema_tables: string[] | null;
}

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sql?: string;
  results?: QueryResultData | null;
  explanation?: string;
  error?: string | null;
  execution_ms?: number;
  timestamp: Date;
}

export type ProcessingStage =
  | "thinking"
  | "schema"
  | "generating"
  | "validating"
  | "executing"
  | "explaining"
  | "done";

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: Date;
}

export interface Settings {
  provider: string;
  model: string;
}
