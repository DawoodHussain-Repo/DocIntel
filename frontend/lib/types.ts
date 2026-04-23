export type MessageRole = "user" | "assistant";

export interface UploadContractData {
  file: string;
  chunks_indexed: number;
  collection: string;
}

export interface UploadedDocument {
  filename: string;
  chunks: number;
}

export interface SuccessResponse<TData> {
  status: "success";
  data: TData;
  message?: string | null;
}

export interface ErrorResponse {
  status: "error";
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
}

export interface ToolCallEvent {
  tool: string;
  query: string;
}

export interface TokenEvent {
  text: string;
}

export interface DoneEvent {
  finish_reason: "stop" | "error" | "timeout";
  error: string | null;
  run_id?: string;
}

export interface StreamHandlers {
  onToolCall: (event: ToolCallEvent) => void;
  onToken: (event: TokenEvent) => void;
  onDone: (event: DoneEvent) => void;
}
