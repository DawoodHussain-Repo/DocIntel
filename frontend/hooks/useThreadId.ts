"use client";

import { useEffect, useState } from "react";
import { THREAD_STORAGE_KEY } from "@/lib/config";

export function useThreadId(): string {
  const [threadId, setThreadId] = useState<string>("");

  useEffect(() => {
    const storedThreadId = sessionStorage.getItem(THREAD_STORAGE_KEY);
    if (storedThreadId) {
      setThreadId(storedThreadId);
      return;
    }

    const generatedThreadId = crypto.randomUUID();
    sessionStorage.setItem(THREAD_STORAGE_KEY, generatedThreadId);
    setThreadId(generatedThreadId);
  }, []);

  return threadId;
}
