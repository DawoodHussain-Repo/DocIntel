"use client";

import { useCallback, useState } from "react";
import { uploadContract } from "@/lib/api";
import { MAX_FILE_SIZE_BYTES } from "@/lib/config";
import { UploadedDocument } from "@/lib/types";

interface UseContractUploadOptions {
  onUploadSuccess: (document: UploadedDocument) => void;
}

export function useContractUpload(options: UseContractUploadOptions) {
  const { onUploadSuccess } = options;
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadFile = useCallback(
    async (file: File): Promise<void> => {
      // Client-side validation
      if (file.type !== "application/pdf") {
        setUploadError("Only PDF files are allowed.");
        return;
      }

      if (file.size > MAX_FILE_SIZE_BYTES) {
        setUploadError(
          `File size exceeds ${MAX_FILE_SIZE_BYTES / 1024 / 1024}MB limit.`
        );
        return;
      }

      if (file.size === 0) {
        setUploadError("File is empty.");
        return;
      }

      setUploadError(null);
      setIsUploading(true);

      try {
        const uploadResult = await uploadContract(file);
        onUploadSuccess({
          filename: uploadResult.file,
          chunks: uploadResult.chunks_indexed,
        });
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Upload failed unexpectedly.";
        setUploadError(message);
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadSuccess],
  );

  return {
    uploadFile,
    isUploading,
    uploadError,
  };
}
