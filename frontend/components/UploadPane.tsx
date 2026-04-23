"use client";

import { useRef, useState } from "react";
import { UploadedDocument } from "@/lib/types";

interface UploadPaneProps {
  documents: UploadedDocument[];
  isUploading: boolean;
  uploadError: string | null;
  onUploadFile: (file: File) => Promise<void>;
  onRemoveDocument: (filename: string) => void;
}

export default function UploadPane(props: UploadPaneProps) {
  const {
    documents,
    isUploading,
    uploadError,
    onUploadFile,
    onRemoveDocument,
  } = props;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState<boolean>(false);

  const handleBrowseClick = (): void => {
    fileInputRef.current?.click();
  };

  const handleFileInput = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ): Promise<void> => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    await onUploadFile(selectedFile);
    event.target.value = "";
  };

  const handleDrop = async (
    event: React.DragEvent<HTMLDivElement>,
  ): Promise<void> => {
    event.preventDefault();
    setIsDragActive(false);

    const droppedFile = event.dataTransfer.files?.[0];
    if (!droppedFile) {
      return;
    }

    await onUploadFile(droppedFile);
  };

  return (
    <aside className="glass-panel sidebar-panel animate-enter-up">
      <header className="sidebar-header">
        <p className="eyebrow">Contract Intelligence</p>
        <h1 className="brand-title">DocIntel Console</h1>
        <p className="brand-subtitle">
          Ingest contracts, validate clauses, and audit evidence with
          citation-grade traceability.
        </p>
      </header>

      <section
        className={`dropzone ${isDragActive ? "dropzone-active" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragActive(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragActive(false);
        }}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleFileInput}
          className="hidden"
        />
        <p className="dropzone-title">Drop contract PDF</p>
        <p className="dropzone-meta">or browse from your secure workspace</p>
        <button
          type="button"
          className="button-secondary"
          onClick={handleBrowseClick}
          disabled={isUploading}
        >
          {isUploading ? "Uploading..." : "Browse File"}
        </button>
      </section>

      {uploadError && <p className="alert-error">{uploadError}</p>}

      <section
        className="document-list-wrapper"
        aria-label="Uploaded documents"
      >
        <div className="section-header">
          <h2>Indexed Documents</h2>
          <span className="section-count">{documents.length}</span>
        </div>

        {documents.length === 0 && (
          <p className="empty-state">No contracts indexed yet.</p>
        )}

        {documents.map((document) => (
          <article key={document.filename} className="document-card">
            <div>
              <p className="document-name">{document.filename}</p>
              <p className="document-meta">{document.chunks} chunks indexed</p>
            </div>
            <button
              type="button"
              className="button-tertiary"
              onClick={() => onRemoveDocument(document.filename)}
            >
              Remove
            </button>
          </article>
        ))}
      </section>
    </aside>
  );
}
