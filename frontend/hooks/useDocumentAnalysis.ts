'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'

import { analyzeDocument } from '@/lib/api'
import { cacheAnalysis, getCachedAnalysis } from '@/lib/file-store'
import { DocumentAnalysisData } from '@/lib/types'

type AnalysisStatus = 'idle' | 'loading' | 'success' | 'error'

export function useDocumentAnalysis(fileName: string | null) {
  const cachedAnalysis = useMemo(
    () => (fileName ? getCachedAnalysis(fileName) : null),
    [fileName],
  )
  const [data, setData] = useState<DocumentAnalysisData | null>(cachedAnalysis)
  const [status, setStatus] = useState<AnalysisStatus>(
    fileName ? (cachedAnalysis ? 'success' : 'loading') : 'idle',
  )
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    setData(cachedAnalysis)
    setStatus(fileName ? (cachedAnalysis ? 'success' : 'loading') : 'idle')
    setError(null)
  }, [cachedAnalysis, fileName])

  useEffect(() => {
    if (!fileName) {
      setStatus('idle')
      setError('Upload a document first to open the workspace.')
      return
    }

    const controller = new AbortController()
    let isMounted = true

    if (!cachedAnalysis) {
      setStatus('loading')
    }

    void (async () => {
      try {
        const nextAnalysis = await analyzeDocument(fileName, {
          signal: controller.signal,
        })
        if (!isMounted) {
          return
        }
        cacheAnalysis(nextAnalysis)
        setData(nextAnalysis)
        setStatus('success')
        setError(null)
      } catch (nextError) {
        if (!isMounted || controller.signal.aborted) {
          return
        }
        setStatus('error')
        setError(
          nextError instanceof Error
            ? nextError.message
            : 'Failed to analyze the document.',
        )
      }
    })()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [cachedAnalysis, fileName, refreshKey])

  const refetch = useCallback(() => {
    setRefreshKey((value) => value + 1)
  }, [])

  return {
    data,
    isLoading: status === 'loading',
    error,
    refetch,
  }
}
