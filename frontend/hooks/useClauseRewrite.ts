'use client'

import { useCallback, useState } from 'react'

import { rewriteClause } from '@/lib/api'
import { RewriteClauseData } from '@/lib/types'

export function useClauseRewrite(fileName: string | null) {
  const [data, setData] = useState<RewriteClauseData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const rewrite = useCallback(
    async (clauseText: string, goal?: string | null) => {
      if (!fileName) {
        setError('Select a document before requesting a clause rewrite.')
        return null
      }

      setIsLoading(true)
      setError(null)
      try {
        const nextData = await rewriteClause({
          file: fileName,
          clause_text: clauseText,
          goal,
        })
        setData(nextData)
        return nextData
      } catch (nextError) {
        setError(
          nextError instanceof Error
            ? nextError.message
            : 'Failed to generate a rewrite.',
        )
        setData(null)
        return null
      } finally {
        setIsLoading(false)
      }
    },
    [fileName],
  )

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return {
    data,
    isLoading,
    error,
    rewrite,
    refetch: reset,
    reset,
  }
}
