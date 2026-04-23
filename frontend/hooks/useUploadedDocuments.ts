"use client";

import { useEffect, useState } from "react";
import { DOC_STORAGE_KEY } from "@/lib/config";
import { UploadedDocument } from "@/lib/types";

function readStoredDocuments(): UploadedDocument[] {
  const rawValue = localStorage.getItem(DOC_STORAGE_KEY);
  if (!rawValue) {
    return [];
  }

  try {
    const parsedValue = JSON.parse(rawValue) as UploadedDocument[];
    if (Array.isArray(parsedValue)) {
      return parsedValue;
    }
    return [];
  } catch {
    return [];
  }
}

export function useUploadedDocuments() {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [hasHydrated, setHasHydrated] = useState<boolean>(false);

  useEffect(() => {
    setDocuments(readStoredDocuments());
    setHasHydrated(true);
  }, []);

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }
    localStorage.setItem(DOC_STORAGE_KEY, JSON.stringify(documents));
  }, [documents, hasHydrated]);

  const addDocument = (document: UploadedDocument): void => {
    setDocuments((previousDocuments) => [document, ...previousDocuments]);
  };

  const removeDocument = (filename: string): void => {
    setDocuments((previousDocuments) =>
      previousDocuments.filter((document) => document.filename !== filename),
    );
  };

  return {
    documents,
    addDocument,
    removeDocument,
  };
}
