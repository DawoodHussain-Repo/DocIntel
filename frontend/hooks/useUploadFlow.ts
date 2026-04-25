'use client'

import { useCallback, useState } from 'react'

import { analyzeDocument, uploadContract } from '@/lib/api'
import { MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '@/lib/config'
import {
  cacheAnalysis,
  cacheUploadedFile,
  getRecentDocuments,
  upsertRecentDocument,
  type RecentDocumentRecord,
} from '@/lib/file-store'
import { UploadStep } from '@/components/UploadProgressModal'

const STEP_LABELS = [
  { key: 'received', label: 'Document received' },
  { key: 'extracting', label: 'Extracting text' },
  { key: 'classifying', label: 'Classifying contract type' },
  { key: 'risk', label: 'Running risk analysis' },
  { key: 'graph', label: 'Building knowledge graph' },
] as const

function buildSteps(activeKey: string, completedKeys: string[] = []): UploadStep[] {
  return STEP_LABELS.map((step) => ({
    key: step.key,
    label: step.label,
    status: completedKeys.includes(step.key)
      ? 'complete'
      : step.key === activeKey
        ? 'active'
        : 'pending',
  }))
}

function isSupportedUpload(file: File): boolean {
  const name = file.name.toLowerCase()
  return (
    file.type === 'application/pdf' ||
    file.type ===
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
    name.endsWith('.pdf') ||
    name.endsWith('.docx')
  )
}

export function useUploadFlow(onSuccess: (fileName: string) => void) {
  const [recentDocuments, setRecentDocuments] = useState<RecentDocumentRecord[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [progressOpen, setProgressOpen] = useState(false)
  const [progressSteps, setProgressSteps] = useState<UploadStep[]>(
    buildSteps('received'),
  )
  const [statusText, setStatusText] = useState('Waiting for a file')
  const [fileName, setFileName] = useState<string | null>(null)

  const refreshRecentDocuments = useCallback(() => {
    setRecentDocuments(getRecentDocuments())
  }, [])

  const startUpload = useCallback(
    async (file: File) => {
      if (!isSupportedUpload(file)) {
        setUploadError('Please upload a PDF or DOCX contract.')
        return
      }

      if (file.size > MAX_FILE_SIZE_BYTES) {
        setUploadError(`File size exceeds the ${MAX_FILE_SIZE_MB}MB limit.`)
        return
      }

      setUploadError(null)
      setFileName(file.name)
      setProgressOpen(true)
      setStatusText('Uploading your document to the analysis engine.')
      setProgressSteps(buildSteps('extracting', ['received']))

      let progressTimer: number | null = null

      try {
        await cacheUploadedFile(file)

        const uploadResult = await uploadContract(file)
        upsertRecentDocument({
          file: uploadResult.file,
          uploadedAt: new Date().toISOString(),
          chunksIndexed: uploadResult.chunks_indexed,
        })
        refreshRecentDocuments()

        const stagedSteps = [
          { activeKey: 'classifying', completedKeys: ['received', 'extracting'] },
          {
            activeKey: 'risk',
            completedKeys: ['received', 'extracting', 'classifying'],
          },
          {
            activeKey: 'graph',
            completedKeys: ['received', 'extracting', 'classifying', 'risk'],
          },
        ]

        let stagedIndex = 0
        setProgressSteps(
          buildSteps(
            stagedSteps[stagedIndex].activeKey,
            stagedSteps[stagedIndex].completedKeys,
          ),
        )
        setStatusText(
          'Generating summary, extraction, risk, and missing-clause checks.',
        )

        progressTimer = window.setInterval(() => {
          stagedIndex = Math.min(stagedIndex + 1, stagedSteps.length - 1)
          const stage = stagedSteps[stagedIndex]
          setProgressSteps(buildSteps(stage.activeKey, stage.completedKeys))
        }, 1500)

        const analysis = await analyzeDocument(uploadResult.file)

        if (progressTimer) {
          window.clearInterval(progressTimer)
        }

        cacheAnalysis(analysis)
        upsertRecentDocument({
          file: analysis.file,
          uploadedAt: new Date().toISOString(),
          chunksIndexed: uploadResult.chunks_indexed,
          contractType: analysis.classification.contract_type,
          riskLevel: analysis.risk.level,
          riskScore: analysis.risk.overall_score,
        })
        refreshRecentDocuments()

        setProgressSteps(
          STEP_LABELS.map((step) => ({
            ...step,
            status: 'complete',
          })),
        )
        setStatusText('Opening the workspace.')
        onSuccess(analysis.file)
      } catch (nextError) {
        if (progressTimer) {
          window.clearInterval(progressTimer)
        }
        setUploadError(
          nextError instanceof Error
            ? nextError.message
            : 'Failed to process the uploaded file.',
        )
        setStatusText('The upload did not finish.')
      }
    },
    [onSuccess, refreshRecentDocuments],
  )

  return {
    data: recentDocuments,
    isLoading: false,
    error: uploadError,
    fileName,
    progressOpen,
    progressSteps,
    refetch: refreshRecentDocuments,
    refreshRecentDocuments,
    setProgressOpen,
    startUpload,
    statusText,
  }
}
