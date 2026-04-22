"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  toolCall?: { tool: string; query: any };
}

interface ChatPaneProps {
  threadId: string;
}

export default function ChatPane({ threadId }: ChatPaneProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentToolCall, setCurrentToolCall] = useState<{
    tool: string;
    query: any;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming || !threadId) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);
    setCurrentToolCall(null);

    // Create assistant message placeholder
    const assistantMessageIndex = messages.length + 1;
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const url = `http://localhost:8000/api/chat/stream?query=${encodeURIComponent(
        userMessage.content
      )}&thread_id=${threadId}`;

      const response = await fetch(url);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            const eventType = line.substring(6).trim();
            const nextLine = lines.shift();

            if (nextLine?.startsWith("data:")) {
              const data = JSON.parse(nextLine.substring(5).trim());

              if (eventType === "tool_call") {
                setCurrentToolCall(data);
              } else if (eventType === "token") {
                setCurrentToolCall(null);
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[assistantMessageIndex] = {
                    ...updated[assistantMessageIndex],
                    content: updated[assistantMessageIndex].content + data.text,
                  };
                  return updated;
                });
              } else if (eventType === "done") {
                setIsStreaming(false);
                setCurrentToolCall(null);
              } else if (eventType === "error") {
                console.error("Stream error:", data.error);
                setIsStreaming(false);
                setCurrentToolCall(null);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error streaming:", error);
      setIsStreaming(false);
      setCurrentToolCall(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderMessageContent = (content: string) => {
    // Replace [Page X] with styled badges
    const parts = content.split(/(\[Page \d+\])/g);

    return (
      <div className="prose prose-sm max-w-none">
        {parts.map((part, idx) => {
          if (part.match(/\[Page \d+\]/)) {
            return (
              <span
                key={idx}
                className="inline-block px-2 py-0.5 mx-1 text-xs font-medium bg-teal-100 text-teal-800 rounded"
              >
                {part}
              </span>
            );
          }
          return <ReactMarkdown key={idx}>{part}</ReactMarkdown>;
        })}
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <h2 className="text-2xl font-semibold mb-2">
              Welcome to DocIntel
            </h2>
            <p>Upload a legal document and ask questions about it</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {msg.role === "user" ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                renderMessageContent(msg.content)
              )}
            </div>
          </div>
        ))}

        {/* Tool Call Badge */}
        {currentToolCall && (
          <div className="flex justify-start">
            <div className="bg-amber-100 border border-amber-300 rounded-lg px-3 py-2 text-xs font-mono text-amber-900">
              [Tool Call: {currentToolCall.tool}(
              {JSON.stringify(currentToolCall.query)})]
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the contract... (Shift+Enter for new line)"
            className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            disabled={isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? "..." : "Send"}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Session ID: {threadId.substring(0, 8)}...
        </p>
      </div>
    </div>
  );
}
