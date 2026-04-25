const defaultBackendUrl = "http://localhost:8000";

function getBackendUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_BACKEND_URL?.trim();

  if (!envUrl) {
    return defaultBackendUrl;
  }

  return envUrl;
}

export const BACKEND_URL = getBackendUrl();
export const MAX_FILE_SIZE_MB = 20;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
export const MAX_QUERY_LENGTH = 2000;
export const QUERY_WARNING_THRESHOLD = 1800;

export const THREAD_STORAGE_KEY = "docintel_thread_id";
export const MESSAGE_STORAGE_PREFIX = "docintel_messages";
