'use client'

import { motion } from 'framer-motion'
import { Wrench } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ReviewItem } from '@/lib/analysis-helpers'

interface ReviewDetailsListProps {
  reviewItems: ReviewItem[]
  setSectionRef: (key: string, node: HTMLDivElement | null) => void
  onRewrite: (item: ReviewItem) => Promise<void>
}

function reviewToneVariant(tone: ReviewItem['tone']) {
  if (tone === 'high') return 'high'
  if (tone === 'medium') return 'medium'
  return 'low'
}

export function ReviewDetailsList({
  reviewItems,
  setSectionRef,
  onRewrite,
}: ReviewDetailsListProps) {
  return (
    <>
      {reviewItems.map((item, index) => (
        <motion.div
          key={item.id}
          ref={(node) => setSectionRef(item.id, node)}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.28, delay: 0.12 + index * 0.06, ease: 'easeOut' }}
          className="card p-6"
        >
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={reviewToneVariant(item.tone)}>
                  {item.kind === 'risk' ? 'Review item' : 'Missing protection'}
                </Badge>
                <p className="label">Evidence-backed</p>
              </div>
              <h3 className="mt-3 font-serif text-2xl text-text">{item.title}</h3>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-text-sub">
                {item.description}
              </p>

              <div className="mt-5 space-y-3">
                {item.evidence.length > 0 ? (
                  item.evidence.map((snippet, evidenceIndex) => (
                    <div key={`${item.id}-${evidenceIndex}`} className="surface-muted px-4 py-4">
                      <div className="flex items-center gap-2">
                        <Badge variant="neutral">Page {snippet.page_number}</Badge>
                        <span className="text-xs text-text-sub">{snippet.heading}</span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-text">{snippet.snippet}</p>
                    </div>
                  ))
                ) : (
                  <div className="surface-muted px-4 py-4 text-sm text-text-sub">
                    No snippet was attached for this item.
                  </div>
                )}
              </div>
            </div>

            <div className="shrink-0">
              <Button variant="primary" onClick={() => void onRewrite(item)}>
                <Wrench className="h-4 w-4" />
                Fix This
              </Button>
            </div>
          </div>
        </motion.div>
      ))}
    </>
  )
}
