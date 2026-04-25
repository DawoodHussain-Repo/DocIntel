"use client";

import { useEffect, useState } from "react";
import { THREAD_STORAGE_KEY } from "@/lib/config";

const UUID_V4_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isValidUuidV4(value: string): boolean {
  return UUID_V4_PATTERN.test(value);
}

export function useThreadId(): string {
  const [threadId, setThreadId] = useState<string>("");

  useEffect(() => {
    const storedThreadId = sessionStorage.getItem(THREAD_STORAGE_KEY);

    if (storedThreadId && isValidUuidV4(storedThreadId)) {
      setThreadId(storedThreadId);
      return;
    }

    const generatedThreadId = crypto.randomUUID();
    sessionStorage.setItem(THREAD_STORAGE_KEY, generatedThreadId);
    setThreadId(generatedThreadId);
  }, []);

  return threadId;
}
