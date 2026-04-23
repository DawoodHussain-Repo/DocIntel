import { BACKEND_URL } from "./config";
import { consumeSseStream } from "./sse";
import {
  ErrorResponse,
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

export async function uploadContract(file: File): Promise<UploadContractData> {
  const requestData = new FormData();
  requestData.append("file", file);

  const response = await fetch(`${BACKEND_URL}/api/upload_contract`, {
    method: "POST",
    body: requestData,
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
  handlers: StreamHandlers,
): Promise<void> {
  const streamUrl = `${BACKEND_URL}/api/chat/stream?query=${encodeURIComponent(
    query,
  )}&thread_id=${encodeURIComponent(threadId)}`;

  const response = await fetch(streamUrl, {
    headers: {
      Accept: "text/event-stream",
    },
  });

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
