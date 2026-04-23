"use client";

import { useEffect, useMemo, useState } from "react";
import { streamChat } from "@/lib/api";
import { MESSAGE_STORAGE_PREFIX } from "@/lib/config";
import { ChatMessage, DoneEvent, ToolCallEvent } from "@/lib/types";

function getStorageKey(threadId: string): string {
  return `${MESSAGE_STORAGE_PREFIX}:${threadId}`;
}

function readStoredMessages(threadId: string): ChatMessage[] {
  const rawValue = sessionStorage.getItem(getStorageKey(threadId));
  if (!rawValue) {
    return [];
  }

  try {
    const parsedMessages = JSON.parse(rawValue) as ChatMessage[];
    return Array.isArray(parsedMessages) ? parsedMessages : [];
  } catch {
    return [];
  }
}

function appendTokenToAssistantMessage(
  currentMessages: ChatMessage[],
  assistantMessageId: string,
  token: string,
): ChatMessage[] {
  return currentMessages.map((message) => {
    if (message.id !== assistantMessageId) {
      return message;
    }

    return {
      ...message,
      content: `${message.content}${token}`,
    };
  });
}

export function useChatStream(threadId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallEvent | null>(
    null,
  );
  const [hasHydrated, setHasHydrated] = useState<boolean>(false);

  useEffect(() => {
    setHasHydrated(false);
    if (!threadId) {
      setMessages([]);
      return;
    }

    setMessages(readStoredMessages(threadId));
    setHasHydrated(true);
  }, [threadId]);

  useEffect(() => {
    if (!threadId || !hasHydrated) {
      return;
    }

    sessionStorage.setItem(getStorageKey(threadId), JSON.stringify(messages));
  }, [messages, threadId, hasHydrated]);

  const canSend = useMemo(
    () => !isStreaming && Boolean(threadId),
    [isStreaming, threadId],
  );

  const sendMessage = async (messageText: string): Promise<void> => {
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || !canSend) {
      return;
    }

    setIsStreaming(true);
    setStreamError(null);
    setCurrentToolCall(null);

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();

    setMessages((previousMessages) => [
      ...previousMessages,
      { id: userMessageId, role: "user", content: trimmedMessage },
      { id: assistantMessageId, role: "assistant", content: "" },
    ]);

    await streamChat(trimmedMessage, threadId, {
      onToolCall: (event: ToolCallEvent) => {
        setCurrentToolCall(event);
      },
      onToken: (event) => {
        setCurrentToolCall(null);
        setMessages((previousMessages) =>
          appendTokenToAssistantMessage(
            previousMessages,
            assistantMessageId,
            event.text,
          ),
        );
      },
      onDone: (event: DoneEvent) => {
        setIsStreaming(false);
        setCurrentToolCall(null);

        if (event.finish_reason === "error") {
          const fallbackMessage =
            event.error ??
            "Streaming failed due to an unexpected backend error.";
          setStreamError(fallbackMessage);
          setMessages((previousMessages) => {
            const hasAssistantContent = previousMessages.some(
              (message) =>
                message.id === assistantMessageId &&
                message.content.trim().length > 0,
            );

            if (hasAssistantContent) {
              return previousMessages;
            }

            return appendTokenToAssistantMessage(
              previousMessages,
              assistantMessageId,
              fallbackMessage,
            );
          });
        } else if (event.finish_reason === "timeout") {
          const timeoutMessage =
            event.error ?? "The agent timed out. Please try again.";
          setStreamError(timeoutMessage);
          setMessages((previousMessages) => {
            const hasAssistantContent = previousMessages.some(
              (message) =>
                message.id === assistantMessageId &&
                message.content.trim().length > 0,
            );

            if (hasAssistantContent) {
              return previousMessages;
            }

            return appendTokenToAssistantMessage(
              previousMessages,
              assistantMessageId,
              timeoutMessage,
            );
          });
        }
      },
    });
  };

  const clearConversation = (): void => {
    setMessages([]);
    setStreamError(null);
    setCurrentToolCall(null);
    if (threadId) {
      sessionStorage.removeItem(getStorageKey(threadId));
    }
  };

  return {
    messages,
    isStreaming,
    streamError,
    currentToolCall,
    sendMessage,
    clearConversation,
  };
}
