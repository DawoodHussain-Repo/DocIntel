'use client'

import { FileWarning } from 'lucide-react'

import { Skeleton } from '@/components/ui/skeleton'

interface DocumentSourcePanelProps {
  pdfPreviewUrl: string | null
  previewState: 'idle' | 'loading' | 'ready' | 'missing' | 'unsupported' | 'error'
  errorMessage?: string | null
}

export function DocumentSourcePanel({
  pdfPreviewUrl,
  previewState,
  errorMessage,
}: DocumentSourcePanelProps) {
  return (
    <section id="document" className="card overflow-hidden">
      <div className="hairline px-6 py-4">
        <p className="label">Source document</p>
        <h2 className="mt-2 font-serif text-2xl text-text">Original file preview</h2>
      </div>

      <div className="p-6">
        {previewState === 'ready' && pdfPreviewUrl ? (
          <iframe
            title="Uploaded PDF preview"
            src={pdfPreviewUrl}
            className="h-[720px] w-full rounded-[22px] border border-border bg-white"
          />
        ) : previewState === 'loading' ? (
          <Skeleton className="h-[720px] w-full rounded-[22px]" />
        ) : previewState === 'unsupported' ? (
          <div className="surface-muted flex h-[280px] flex-col items-center justify-center px-8 text-center">
            <FileWarning className="h-8 w-8 text-text-sub" />
            <p className="mt-4 text-sm font-medium text-text">Preview is currently PDF only</p>
            <p className="mt-2 max-w-md text-sm leading-6 text-text-sub">
              The backend analysis still works for DOCX uploads, but in-app preview is reserved for PDFs in the current MVP.
            </p>
          </div>
        ) : previewState === 'error' ? (
          <div className="surface-muted flex h-[280px] flex-col items-center justify-center px-8 text-center">
            <FileWarning className="h-8 w-8 text-danger" />
            <p className="mt-4 text-sm font-medium text-text">Preview failed to load</p>
            <p className="mt-2 max-w-md text-sm leading-6 text-text-sub">
              {errorMessage ?? 'The cached preview could not be restored in this session.'}
            </p>
          </div>
        ) : (
          <div className="surface-muted flex h-[280px] flex-col items-center justify-center px-8 text-center">
            <FileWarning className="h-8 w-8 text-text-sub" />
            <p className="mt-4 text-sm font-medium text-text">Preview unavailable in this session</p>
            <p className="mt-2 max-w-md text-sm leading-6 text-text-sub">
              The analysis is available, but the original file is no longer cached locally. Upload the PDF again to restore the embedded preview.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
