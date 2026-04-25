import { BACKEND_URL } from "./config";
import { consumeSseStream } from "./sse";
import {
  DocumentAnalysisData,
  ErrorResponse,
  RewriteClauseData,
  StreamHandlers,
  SuccessResponse,
  UploadContractData,
} from "./types";

function getErrorMessage(payload: unknown): string {
  if (typeof payload !== "object" || payload === null) {
    return "Request failed.";
  }

  const maybeError = payload as Partial<ErrorResponse>;
  if (typeof maybeError.error === "string" && maybeError.error.length > 0) {
    return maybeError.error;
  }

  return "Request failed.";
}

interface RequestOptions {
  signal?: AbortSignal;
}

export async function uploadContract(
  file: File,
  options: RequestOptions = {},
): Promise<UploadContractData> {
  const requestData = new FormData();
  requestData.append("file", file);

  const response = await fetch(`${BACKEND_URL}/api/upload_contract`, {
    method: "POST",
    body: requestData,
    signal: options.signal,
  });

  const payload = (await response.json()) as
    | SuccessResponse<UploadContractData>
    | ErrorResponse;

  if (!response.ok || payload.status !== "success") {
    throw new Error(getErrorMessage(payload));
  }

  return payload.data;
}

export async function streamChat(
  query: string,
  threadId: string,
  file: string | null,
  handlers: StreamHandlers,
  options: RequestOptions = {},
): Promise<void> {
  const fileParam = file ? `&file=${encodeURIComponent(file)}` : "";
  const streamUrl = `${BACKEND_URL}/api/chat/stream?query=${encodeURIComponent(
    query,
  )}&thread_id=${encodeURIComponent(threadId)}${fileParam}`;

  let response: Response;
  try {
    response = await fetch(streamUrl, {
      headers: {
        Accept: "text/event-stream",
      },
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }
    handlers.onDone({
      finish_reason: "error",
      error: "Failed to start chat stream.",
    });
    return;
  }

  if (!response.ok) {
    let errorMessage = "Failed to start chat stream.";
    try {
      const payload = (await response.json()) as ErrorResponse;
      errorMessage = getErrorMessage(payload);
    } catch {
      errorMessage = `Failed to start chat stream (${response.status}).`;
    }
    handlers.onDone({ finish_reason: "error", error: errorMessage });
    return;
  }

  await consumeSseStream(response, handlers);
}

export async function analyzeDocument(
  file: string,
  options: RequestOptions = {},
): Promise<DocumentAnalysisData> {
  const response = await fetch(`${BACKEND_URL}/api/analyze_document`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ file }),
    signal: options.signal,
  });

  const payload = (await response.json()) as
    | SuccessResponse<DocumentAnalysisData>
    | ErrorResponse;

  if (!response.ok || payload.status !== "success") {
    throw new Error(getErrorMessage(payload));
  }

  return payload.data;
}

export async function rewriteClause(params: {
  file: string;
  clause_text: string;
  goal?: string | null;
}, options: RequestOptions = {}): Promise<RewriteClauseData> {
  const response = await fetch(`${BACKEND_URL}/api/rewrite_clause`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
    signal: options.signal,
  });

  const payload = (await response.json()) as
    | SuccessResponse<RewriteClauseData>
    | ErrorResponse;

  if (!response.ok || payload.status !== "success") {
    throw new Error(getErrorMessage(payload));
  }

  return payload.data;
}
