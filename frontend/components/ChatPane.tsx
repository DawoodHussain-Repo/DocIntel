"use client";

import { useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { MAX_QUERY_LENGTH, QUERY_WARNING_THRESHOLD } from "@/lib/config";
import { ChatMessage, ToolCallEvent } from "@/lib/types";

interface ChatPaneProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamError: string | null;
  currentToolCall: ToolCallEvent | null;
  threadId: string;
  onSendMessage: (messageText: string) => Promise<void>;
  onClearConversation: () => void;
}

function renderAssistantMessage(content: string): React.ReactNode {
  const parts = content.split(/(\[Page\s+\d+\])/g);

  return parts.map((part, index) => {
    if (/\[Page\s+\d+\]/.test(part)) {
      return (
        <span key={`citation-${index}`} className="citation-pill">
          {part}
        </span>
      );
    }

    return (
      <ReactMarkdown key={`chunk-${index}`} className="markdown-chunk">
        {part}
      </ReactMarkdown>
    );
  });
}

export default function ChatPane(props: ChatPaneProps) {
  const {
    messages,
    isStreaming,
    streamError,
    currentToolCall,
    threadId,
    onSendMessage,
    onClearConversation,
  } = props;

  const [draftMessage, setDraftMessage] = useState<string>("");
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const shortThreadId = useMemo(() => threadId.slice(0, 8), [threadId]);
  
  const queryLength = draftMessage.length;
  const showCharacterCount = queryLength > QUERY_WARNING_THRESHOLD;
  const isQueryTooLong = queryLength > MAX_QUERY_LENGTH;
  const canSend = !isStreaming && !isQueryTooLong && draftMessage.trim().length > 0 && threadId;

  const handleSend = async (): Promise<void> => {
    const trimmedMessage = draftMessage.trim();
    if (!trimmedMessage || isStreaming || !threadId || isQueryTooLong) {
      return;
    }

    setDraftMessage("");
    await onSendMessage(trimmedMessage);
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="glass-panel chat-panel animate-enter-up">
      <header className="chat-header">
        <div>
          <p className="eyebrow">Live Agent</p>
          <h2 className="chat-title">Clause Intelligence Stream</h2>
        </div>
        <button
          type="button"
          className="button-secondary"
          onClick={onClearConversation}
        >
          Clear Conversation
        </button>
      </header>

      <main className="message-scroll-region" aria-live="polite">
        {messages.length === 0 && (
          <div className="hero-empty">
            <h3>Ready for document-grounded Q&A</h3>
            <p>
              Ask for obligations, liabilities, renewal terms, or edge-case
              clauses.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <article
            key={message.id}
            className={`message-row ${message.role === "user" ? "from-user" : "from-assistant"}`}
          >
            <div className="message-card">
              {message.role === "assistant" ? (
                <div className="message-markdown">
                  {renderAssistantMessage(message.content)}
                </div>
              ) : (
                <p>{message.content}</p>
              )}
            </div>
          </article>
        ))}

        {currentToolCall && (
          <div className="tool-call-badge">
            Tool call: {currentToolCall.tool}({currentToolCall.query})
          </div>
        )}

        {streamError && <p className="alert-error">{streamError}</p>}
        <div ref={endOfMessagesRef} />
      </main>

      <footer className="composer-shell">
        <label htmlFor="messageInput" className="sr-only">
          Ask a contract question
        </label>
        <textarea
          id="messageInput"
          value={draftMessage}
          onChange={(event) => setDraftMessage(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
          placeholder="Ask a question about contractual obligations or risk exposure..."
          className="composer-input"
          rows={3}
          disabled={isStreaming}
        />
        <div className="composer-actions">
          <p className="thread-chip">Thread {shortThreadId || "pending"}</p>
          {showCharacterCount && (
            <p
              className={`text-xs ${isQueryTooLong ? "text-red-400" : "text-amber-400"}`}
            >
              {queryLength}/{MAX_QUERY_LENGTH}
            </p>
          )}
          <button
            type="button"
            className="button-primary"
            onClick={() => void handleSend()}
            disabled={!canSend}
          >
            {isStreaming ? "Streaming..." : "Send"}
          </button>
        </div>
      </footer>
    </section>
  );
}
