import { logger } from "./logger";
import { DoneEvent, StreamHandlers, TokenEvent, ToolCallEvent } from "./types";

function reportSseError(message: string, error: unknown): void {
  logger.error(message, error);
}

function parseJsonSafely<T>(rawValue: string): T | null {
  try {
    return JSON.parse(rawValue) as T;
  } catch (error) {
    reportSseError("Failed to parse SSE JSON:", error);
    return null;
  }
}

function dispatchEvent(
  eventName: string,
  dataLines: string[],
  handlers: StreamHandlers,
): void {
  if (dataLines.length === 0) {
    return;
  }

  const rawPayload = dataLines.join("\n");
  
  try {
    if (eventName === "tool_call") {
      const payload = parseJsonSafely<ToolCallEvent>(rawPayload);
      if (payload) {
        handlers.onToolCall(payload);
      }
    }

    if (eventName === "token") {
      const payload = parseJsonSafely<TokenEvent>(rawPayload);
      if (payload) {
        handlers.onToken(payload);
      }
    }

    if (eventName === "done") {
      const payload = parseJsonSafely<DoneEvent>(rawPayload);
      if (payload) {
        handlers.onDone(payload);
        return;
      }

      handlers.onDone({ finish_reason: "error", error: "Malformed done event.", run_id: undefined });
    }
  } catch (error) {
    reportSseError("Error dispatching SSE event:", error);
  }
}

export async function consumeSseStream(
  response: Response,
  handlers: StreamHandlers,
): Promise<void> {
  const streamReader = response.body?.getReader();
  if (!streamReader) {
    handlers.onDone({
      finish_reason: "error",
      error: "No stream reader available.",
      run_id: undefined,
    });
    return;
  }

  const decoder = new TextDecoder();
  let pendingText = "";
  let eventName = "message";
  let dataLines: string[] = [];

  try {
    while (true) {
      const { done, value } = await streamReader.read();
      if (done) {
        break;
      }

      pendingText += decoder.decode(value, { stream: true });
      let lineBreakIndex = pendingText.indexOf("\n");

      while (lineBreakIndex >= 0) {
        const rawLine = pendingText.slice(0, lineBreakIndex);
        pendingText = pendingText.slice(lineBreakIndex + 1);
        const line = rawLine.replace(/\r$/, "");

        if (line === "") {
          dispatchEvent(eventName, dataLines, handlers);
          eventName = "message";
          dataLines = [];
        } else if (line.startsWith("event:")) {
          eventName = line.replace("event:", "").trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.replace("data:", "").trim());
        }

        lineBreakIndex = pendingText.indexOf("\n");
      }
    }

    if (pendingText.length > 0) {
      const trailingLine = pendingText.replace(/\r$/, "");
      if (trailingLine.startsWith("data:")) {
        dataLines.push(trailingLine.replace("data:", "").trim());
      }
    }

    dispatchEvent(eventName, dataLines, handlers);
  } catch (error) {
    reportSseError("SSE stream error:", error);
    handlers.onDone({
      finish_reason: "error",
      error: "Stream connection failed.",
      run_id: undefined,
    });
  } finally {
    streamReader.releaseLock();
  }
}
