"use client";

import { useCallback, useState } from "react";
import { uploadContract } from "@/lib/api";
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
      if (file.type !== "application/pdf") {
        setUploadError("Only PDF files are allowed.");
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
