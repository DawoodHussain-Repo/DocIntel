'use client'

import { Suspense, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { useSearchParams } from 'next/navigation'

import { AnalysisHero } from '@/components/features/workspace/analysis-hero'
import { ChatPanel } from '@/components/features/workspace/chat-panel'
import { ClauseMapPanel } from '@/components/features/workspace/clause-map-panel'
import { DocumentRail } from '@/components/features/workspace/document-rail'
import { DocumentSourcePanel } from '@/components/features/workspace/document-source-panel'
import { FindingsBoard } from '@/components/features/workspace/findings-board'
import { KeyDetailsPanel } from '@/components/features/workspace/key-details-panel'
import { ReviewDetailsList } from '@/components/features/workspace/review-details-list'
import { RewriteClauseDialog } from '@/components/features/workspace/rewrite-clause-dialog'
import { buildReviewItems, groupExtractedFields, type ReviewItem } from '@/lib/analysis-helpers'
import { MAX_QUERY_LENGTH } from '@/lib/config'
import { getRecentDocuments } from '@/lib/file-store'
import { useClauseRewrite } from '@/hooks/useClauseRewrite'
import { useChatStream } from '@/hooks/useChatStream'
import { useDocumentAnalysis } from '@/hooks/useDocumentAnalysis'
import { useDocumentPreview } from '@/hooks/useDocumentPreview'
import { useThreadId } from '@/hooks/useThreadId'

function WorkspaceContent() {
  const searchParams = useSearchParams()
  const requestedFile = searchParams.get('file')
  const fallbackFile = getRecentDocuments()[0]?.file ?? null
  const activeFile = requestedFile ?? fallbackFile

  const { data: analysis, isLoading, error: analysisError } = useDocumentAnalysis(activeFile)
  const { data: pdfPreviewUrl, status: previewState, error: previewError } =
    useDocumentPreview(activeFile)

  const [rewriteOpen, setRewriteOpen] = useState(false)
  const [rewriteTitle, setRewriteTitle] = useState('')
  const [rewriteOriginal, setRewriteOriginal] = useState('')
  const [rewriteReplacement, setRewriteReplacement] = useState('')
  const [rewriteReason, setRewriteReason] = useState('')
  const { isLoading: isRewriting, rewrite, reset: resetRewrite } = useClauseRewrite(activeFile)

  const threadId = useThreadId()
  const { messages, isStreaming, streamError, currentToolCall, sendMessage, clearConversation } =
    useChatStream(threadId, activeFile)
  const [draftMessage, setDraftMessage] = useState('')

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({})

  const reviewItems = analysis ? buildReviewItems(analysis) : []
  const clauseItems = analysis?.clauses ?? []
  const fieldSections = analysis ? groupExtractedFields(analysis) : []
  const missingProtections = analysis?.missing_clauses.filter((item) => !item.present) ?? []

  const openRewriteModal = async (item: ReviewItem) => {
    if (!activeFile) {
      return
    }

    const evidenceText =
      item.evidence.map((snippet) => snippet.snippet).join('\n\n') || item.description

    setRewriteTitle(item.title)
    setRewriteOriginal(evidenceText)
    setRewriteReplacement('')
    setRewriteReason('')
    resetRewrite()
    setRewriteOpen(true)

    const response = await rewrite(evidenceText, null)
    if (response) {
      setRewriteReplacement(response.replacement_clause)
      setRewriteReason(response.rationale)
      return
    }

    setRewriteReplacement('Failed to generate a rewrite.')
    setRewriteReason('')
  }

  const setSectionRef = (key: string, node: HTMLDivElement | null) => {
    sectionRefs.current[key] = node
  }

  const scrollToSection = (key: string) => {
    const element = sectionRefs.current[key] ?? document.getElementById(key)
    if (!element) {
      return
    }

    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleSendMessage = async () => {
    const nextMessage = draftMessage.trim()
    if (!nextMessage || !activeFile || nextMessage.length > MAX_QUERY_LENGTH) {
      return
    }

    setDraftMessage('')
    await sendMessage(nextMessage)
  }

  return (
    <main className="mx-auto max-w-[1600px] px-6 py-8 md:px-8 lg:px-10">
      <div className="grid gap-10 xl:grid-cols-[minmax(0,1fr)_400px]">
        <section className="min-w-0 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.32, ease: 'easeOut' }}
          >
            <AnalysisHero
              activeFile={activeFile}
              analysis={analysis ?? null}
              isLoading={isLoading}
              error={analysisError}
            />
          </motion.div>

          <div className="grid gap-6 2xl:grid-cols-[280px_minmax(0,1fr)]">
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.32, delay: 0.04, ease: 'easeOut' }}
            >
              <DocumentRail
                activeFile={activeFile}
                contractType={analysis?.classification.contract_type}
                riskLevel={analysis?.risk.level}
                riskScore={analysis?.risk.overall_score}
                clauseItems={clauseItems}
                flaggedItems={reviewItems}
                onJump={scrollToSection}
              />
            </motion.div>

            <div className="min-w-0 space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.32, delay: 0.06, ease: 'easeOut' }}
              >
                <FindingsBoard
                  clauseItems={clauseItems}
                  flaggedItems={reviewItems}
                  missingProtections={missingProtections}
                  onJump={scrollToSection}
                  onRewrite={openRewriteModal}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.32, delay: 0.08, ease: 'easeOut' }}
              >
                <KeyDetailsPanel
                  isLoading={isLoading}
                  fieldSections={fieldSections}
                  missingProtections={missingProtections}
                  contractType={analysis?.classification.contract_type}
                />
              </motion.div>

              <ReviewDetailsList
                reviewItems={reviewItems}
                setSectionRef={setSectionRef}
                onRewrite={openRewriteModal}
              />

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.32, delay: 0.12, ease: 'easeOut' }}
              >
                <ClauseMapPanel clauseItems={clauseItems} setSectionRef={setSectionRef} />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.32, delay: 0.14, ease: 'easeOut' }}
              >
                <DocumentSourcePanel
                  pdfPreviewUrl={pdfPreviewUrl}
                  previewState={previewState}
                  errorMessage={previewError}
                />
              </motion.div>
            </div>
          </div>
        </section>

        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.32, delay: 0.06, ease: 'easeOut' }}
        >
          <ChatPanel
            activeFile={activeFile}
            contractType={analysis?.classification.contract_type}
            riskLevel={analysis?.risk.level}
            riskScore={analysis?.risk.overall_score}
            messages={messages}
            isStreaming={isStreaming}
            streamError={streamError}
            currentToolCall={currentToolCall}
            draftMessage={draftMessage}
            onDraftChange={setDraftMessage}
            onSend={handleSendMessage}
            onClear={clearConversation}
          />
        </motion.div>
      </div>

      <RewriteClauseDialog
        open={rewriteOpen}
        onOpenChange={setRewriteOpen}
        title={rewriteTitle}
        original={rewriteOriginal}
        replacement={rewriteReplacement}
        rationale={rewriteReason}
        isLoading={isRewriting}
      />
    </main>
  )
}

export default function WorkspacePage() {
  return (
    <Suspense>
      <WorkspaceContent />
    </Suspense>
  )
}
