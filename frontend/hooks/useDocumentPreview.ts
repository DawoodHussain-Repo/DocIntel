'use client'

import { useEffect, useState } from 'react'

import { loadCachedDocument } from '@/lib/file-store'

export type PreviewStatus =
  | 'idle'
  | 'loading'
  | 'ready'
  | 'missing'
  | 'unsupported'
  | 'error'

export function useDocumentPreview(fileName: string | null) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [status, setStatus] = useState<PreviewStatus>('idle')

  useEffect(() => {
    if (!fileName) {
      setPreviewUrl(null)
      setStatus('missing')
      return
    }

    let objectUrl: string | null = null
    let isMounted = true
    setStatus('loading')

    void (async () => {
      try {
        const cachedDocument = await loadCachedDocument(fileName)
        if (!isMounted) {
          return
        }

        if (!cachedDocument) {
          setPreviewUrl(null)
          setStatus('missing')
          return
        }

        if (cachedDocument.contentType !== 'application/pdf') {
          setPreviewUrl(null)
          setStatus('unsupported')
          return
        }

        objectUrl = URL.createObjectURL(cachedDocument.blob)
        setPreviewUrl(objectUrl)
        setStatus('ready')
      } catch {
        if (!isMounted) {
          return
        }
        setPreviewUrl(null)
        setStatus('error')
      }
    })()

    return () => {
      isMounted = false
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [fileName])

  return {
    data: previewUrl,
    isLoading: status === 'loading',
    error: status === 'error' ? 'Failed to load the cached document preview.' : null,
    status,
    refetch: () => undefined,
  }
}
