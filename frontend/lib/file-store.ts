import { DocumentAnalysisData } from "@/lib/types";

const DATABASE_NAME = "docintel-upload-cache";
const STORE_NAME = "documents";
const RECENT_DOCUMENTS_KEY = "docintel_recent_documents";
const ANALYSIS_CACHE_PREFIX = "docintel_analysis:";

export interface RecentDocumentRecord {
  file: string;
  uploadedAt: string;
  contractType?: DocumentAnalysisData["classification"]["contract_type"];
  riskLevel?: DocumentAnalysisData["risk"]["level"];
  riskScore?: number;
  chunksIndexed?: number;
}

export interface CachedDocumentRecord {
  file: string;
  blob: Blob;
  contentType: string;
  uploadedAt: string;
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!isBrowser()) {
      reject(new Error("IndexedDB is unavailable on the server."));
      return;
    }

    const request = window.indexedDB.open(DATABASE_NAME, 1);

    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "file" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(request.error ?? new Error("Failed to open IndexedDB."));
  });
}

export async function cacheUploadedFile(file: File): Promise<void> {
  const database = await openDatabase();

  await new Promise<void>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);

    store.put({
      file: file.name,
      blob: file,
      contentType: file.type,
      uploadedAt: new Date().toISOString(),
    } satisfies CachedDocumentRecord);

    transaction.oncomplete = () => resolve();
    transaction.onerror = () =>
      reject(transaction.error ?? new Error("Failed to cache uploaded file."));
  });

  database.close();
}

export async function loadCachedFile(fileName: string): Promise<Blob | null> {
  const record = await loadCachedDocument(fileName);
  return record?.blob ?? null;
}

export async function loadCachedDocument(
  fileName: string,
): Promise<CachedDocumentRecord | null> {
  const database = await openDatabase();

  const record = await new Promise<CachedDocumentRecord | null>((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readonly");
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(fileName);

    request.onsuccess = () => {
      if (!request.result) {
        resolve(null);
        return;
      }

      resolve(request.result as CachedDocumentRecord);
    };
    request.onerror = () =>
      reject(request.error ?? new Error("Failed to load cached file."));
  });

  database.close();
  return record;
}

export function getRecentDocuments(): RecentDocumentRecord[] {
  if (!isBrowser()) {
    return [];
  }

  try {
    const rawValue = window.localStorage.getItem(RECENT_DOCUMENTS_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue) as RecentDocumentRecord[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function upsertRecentDocument(record: RecentDocumentRecord): void {
  if (!isBrowser()) {
    return;
  }

  const nextRecords = [
    record,
    ...getRecentDocuments().filter((item) => item.file !== record.file),
  ].slice(0, 8);

  window.localStorage.setItem(RECENT_DOCUMENTS_KEY, JSON.stringify(nextRecords));
}

export function getCachedAnalysis(fileName: string): DocumentAnalysisData | null {
  if (!isBrowser()) {
    return null;
  }

  try {
    const rawValue = window.sessionStorage.getItem(`${ANALYSIS_CACHE_PREFIX}${fileName}`);
    if (!rawValue) {
      return null;
    }

    return JSON.parse(rawValue) as DocumentAnalysisData;
  } catch {
    return null;
  }
}

export function cacheAnalysis(analysis: DocumentAnalysisData): void {
  if (!isBrowser()) {
    return;
  }

  window.sessionStorage.setItem(
    `${ANALYSIS_CACHE_PREFIX}${analysis.file}`,
    JSON.stringify(analysis),
  );
}
