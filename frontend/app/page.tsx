"use client";

import { useState, useEffect, useRef } from "react";
import UploadPane from "./components/UploadPane";
import ChatPane from "./components/ChatPane";

export default function Home() {
  const [uploadedDocs, setUploadedDocs] = useState<
    Array<{ filename: string; chunks: number }>
  >([]);
  const [threadId, setThreadId] = useState<string>("");

  useEffect(() => {
    // Generate or retrieve thread_id from sessionStorage
    let storedThreadId = sessionStorage.getItem("docintel_thread_id");
    if (!storedThreadId) {
      storedThreadId = crypto.randomUUID();
      sessionStorage.setItem("docintel_thread_id", storedThreadId);
    }
    setThreadId(storedThreadId);
  }, []);

  const handleUploadSuccess = (filename: string, chunks: number) => {
    setUploadedDocs((prev) => [...prev, { filename, chunks }]);
  };

  const handleRemoveDoc = (filename: string) => {
    setUploadedDocs((prev) => prev.filter((doc) => doc.filename !== filename));
  };

  return (
    <div className="flex h-screen w-screen">
      <UploadPane
        uploadedDocs={uploadedDocs}
        onUploadSuccess={handleUploadSuccess}
        onRemoveDoc={handleRemoveDoc}
      />
      <ChatPane threadId={threadId} />
    </div>
  );
}
