'use client'

import { startTransition, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import {
  ArrowUpRight,
  Clock3,
  FileText,
  FileUp,
  FolderOpen,
  Scale,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { UploadProgressModal } from '@/components/UploadProgressModal'
import { Badge } from '@/components/ui/badge'
import { useUploadFlow } from '@/hooks/useUploadFlow'
import { RecentDocumentRecord } from '@/lib/file-store'
import { cn } from '@/lib/utils'

function riskBadgeVariant(riskLevel?: RecentDocumentRecord['riskLevel']) {
  if (riskLevel === 'red') return 'high'
  if (riskLevel === 'yellow') return 'medium'
  if (riskLevel === 'green') return 'low'
  return 'neutral'
}

export default function HomePage() {
  const router = useRouter()
  const [isDragActive, setIsDragActive] = useState(false)
  const {
    data: recentDocuments,
    error: uploadError,
    fileName,
    progressOpen,
    progressSteps,
    refreshRecentDocuments,
    setProgressOpen,
    startUpload,
    statusText,
  } = useUploadFlow((nextFile) => {
    window.setTimeout(() => {
      startTransition(() => {
        router.push(`/workspace?file=${encodeURIComponent(nextFile)}`)
      })
    }, 250)
  })

  useEffect(() => {
    refreshRecentDocuments()
  }, [refreshRecentDocuments])

  return (
    <main className="mx-auto max-w-[1600px] px-6 py-8 md:px-8 lg:px-10">
      <div className="grid gap-10 lg:grid-cols-12">
        {/* Left Column - Upload */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="lg:col-span-8"
        >
          <div className="overflow-hidden rounded-3xl border border-border bg-white shadow-card">
            <div className="p-10 pb-8 border-b border-slate-100">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-accent" />
                <h2 className="text-xs font-bold tracking-widest text-accent uppercase">
                  AI Document Analysis
                </h2>
              </div>
              <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">
                Your contract, reviewed with the live engine
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-text-sub">
                Upload a PDF or Word document. The backend ingests it, then you get
                summary, extracted terms, risk review, rewrites, and grounded chat.
              </p>
            </div>

            <div className="p-10">
              <div
                className={cn(
                  'rounded-3xl border-2 border-dashed px-8 py-14 text-center transition-all',
                  isDragActive
                    ? 'animate-pulse-border border-accent bg-accent/[0.04] shadow-[0_0_0_6px_rgba(79,70,229,0.08)]'
                    : 'border-slate-300 bg-slate-50/50',
                )}
                onDragOver={(event) => {
                  event.preventDefault()
                  setIsDragActive(true)
                }}
                onDragLeave={(event) => {
                  event.preventDefault()
                  setIsDragActive(false)
                }}
                onDrop={(event) => {
                  event.preventDefault()
                  setIsDragActive(false)
                  const file = event.dataTransfer.files?.[0]
                  if (!file) {
                    return
                  }
                  void startUpload(file)
                }}
              >
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-900">
                  <FileUp className="h-6 w-6 text-white" />
                </div>
                <h2 className="mt-5 text-2xl font-semibold text-slate-900">Drop a PDF to begin</h2>
                <p className="mt-2 text-sm text-text-sub">
                  The first pass is wired to the live FastAPI backend.
                </p>

                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  <label className="inline-flex">
                    <input
                      className="sr-only"
                      type="file"
                      accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={(event) => {
                        const selectedFile = event.target.files?.[0]
                        if (!selectedFile) {
                          return
                        }
                        void startUpload(selectedFile)
                        event.target.value = ''
                      }}
                    />
                    <span className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-800">
                      <FileUp className="h-4 w-4" />
                      Choose file
                    </span>
                  </label>

                  <div className="inline-flex items-center gap-2 rounded-xl border border-border bg-white px-4 py-2.5 text-sm text-text-sub">
                    <FileText className="h-4 w-4" />
                    PDF or DOCX
                  </div>
                </div>
              </div>

              {uploadError ? (
                <div className="mt-4 rounded-xl border border-danger/20 bg-danger/5 px-4 py-3 text-sm text-danger">
                  {uploadError}
                </div>
              ) : null}

              <div className="mt-8 flex flex-wrap gap-3">
                <Badge variant="neutral">
                  <FileText className="mr-1 h-3.5 w-3.5" />
                  3-5 bullet summary
                </Badge>
                <Badge variant="neutral">
                  <Scale className="mr-1 h-3.5 w-3.5" />
                  Clause extraction + risk
                </Badge>
                <Badge variant="neutral">
                  <ShieldCheck className="mr-1 h-3.5 w-3.5" />
                  Rewrite + chat
                </Badge>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Right Column - Recent Files */}
        <motion.aside
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.08, ease: 'easeOut' }}
          className="lg:col-span-4"
        >
          <div className="rounded-3xl border border-border bg-white shadow-card p-8">
            <div className="flex items-center justify-between">
              <div>
                <p className="label">Recent files</p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">Continue where you left off</h2>
              </div>
              <FolderOpen className="h-5 w-5 text-text-sub" />
            </div>

            <div className="mt-6 space-y-3">
              {recentDocuments.length === 0 ? (
                <div className="surface-muted px-4 py-5 text-sm text-text-sub">
                  Uploaded documents appear here after the first successful run.
                </div>
              ) : (
                recentDocuments.map((document) => (
                  <button
                    key={document.file}
                    type="button"
                    onClick={() =>
                      router.push(`/workspace?file=${encodeURIComponent(document.file)}`)
                    }
                    className="flex w-full items-start justify-between rounded-2xl border border-border bg-white px-4 py-4 text-left transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-sm group"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-text group-hover:text-accent transition-colors">
                        {document.file}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-text-sub">
                        <span className="inline-flex items-center gap-1">
                          <Clock3 className="h-3.5 w-3.5" />
                          {new Date(document.uploadedAt).toLocaleString()}
                        </span>
                        {document.contractType ? (
                          <Badge variant="type">{document.contractType}</Badge>
                        ) : null}
                        {typeof document.riskScore === 'number' ? (
                          <Badge variant={riskBadgeVariant(document.riskLevel)}>
                            {document.riskScore}
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                    <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-300 group-hover:text-accent transition-colors" />
                  </button>
                ))
              )}
            </div>

            <div className="surface-muted mt-6 px-4 py-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-accent" />
                <p className="text-sm font-medium text-text">Live backend flow</p>
              </div>
              <p className="mt-2 text-sm leading-6 text-text-sub">
                The frontend now expects the FastAPI server on <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">NEXT_PUBLIC_BACKEND_URL</code> and keeps your uploaded PDF cached locally for workspace preview.
              </p>
            </div>
          </div>
        </motion.aside>
      </div>

      <UploadProgressModal
        open={progressOpen}
        onOpenChange={setProgressOpen}
        fileName={fileName}
        steps={progressSteps}
        statusText={statusText}
        errorText={uploadError}
      />
    </main>
  )
}
