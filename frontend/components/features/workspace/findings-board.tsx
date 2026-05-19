'use client'

import { AlertTriangle, CheckCircle2, Minus, ShieldAlert, Wrench } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ClauseNode, MissingClause } from '@/lib/types'
import type { ReviewItem } from '@/lib/analysis-helpers'

interface FindingsBoardProps {
  clauseItems: ClauseNode[]
  flaggedItems: ReviewItem[]
  missingProtections: MissingClause[]
  onJump: (sectionId: string) => void
  onRewrite: (item: ReviewItem) => Promise<void>
}

function reviewToneVariant(tone: ReviewItem['tone']) {
  if (tone === 'high') return 'high'
  if (tone === 'medium') return 'medium'
  return 'low'
}

interface FindingsSectionProps {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}

function FindingsSection({ title, icon, children }: FindingsSectionProps) {
  return (
    <div className="flex items-start gap-6">
      <div className="mt-1 shrink-0 rounded-2xl bg-slate-50 p-3">
        {icon}
      </div>
      <div className="flex-1">
        <h4 className="text-lg font-medium text-slate-900 mb-4">{title}</h4>
        {children}
      </div>
    </div>
  )
}

export function FindingsBoard({
  clauseItems,
  flaggedItems,
  missingProtections,
  onJump,
  onRewrite,
}: FindingsBoardProps) {
  const safeClauses = clauseItems.filter((clause) => clause.risk_level === 'green').slice(0, 4)
  const reviewClauses = flaggedItems.filter((item) => item.kind === 'risk').slice(0, 4)
  const missingItems = missingProtections.slice(0, 4)

  return (
    <section id="findings" className="card p-10 overflow-hidden">
      <h3 className="label mb-8">Detailed Breakdown</h3>

      <div className="space-y-12">
        {/* Protective Areas */}
        <FindingsSection
          title="Protective Areas"
          icon={<CheckCircle2 size={24} className="text-emerald-500" />}
        >
          <ul className="space-y-4">
            {safeClauses.length > 0 ? (
              safeClauses.map((clause) => (
                <li key={clause.id} className="flex items-start gap-3 group">
                  <Minus
                    size={16}
                    className="text-slate-300 mt-1 flex-shrink-0 group-hover:text-accent transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => onJump(`clause-${clause.id}`)}
                    className="text-left text-slate-600 leading-relaxed font-light hover:text-text transition-colors"
                  >
                    <span className="font-medium text-text">{clause.title}:</span>{' '}
                    {clause.text.slice(0, 180)}
                    {clause.text.length > 180 ? '…' : ''}
                  </button>
                </li>
              ))
            ) : (
              <li className="text-sm text-text-sub">No low-risk clauses were identified yet.</li>
            )}
          </ul>
        </FindingsSection>

        {/* Watch Items */}
        <FindingsSection
          title="Watch Items"
          icon={<AlertTriangle size={24} className="text-amber-500" />}
        >
          <ul className="space-y-4">
            {reviewClauses.length > 0 ? (
              reviewClauses.map((item) => (
                <li key={item.id} className="flex items-start gap-3 group">
                  <Minus
                    size={16}
                    className="text-slate-300 mt-1 flex-shrink-0 group-hover:text-amber-400 transition-colors"
                  />
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <button
                        type="button"
                        onClick={() => onJump(item.id)}
                        className="text-left text-slate-600 leading-relaxed font-light hover:text-text transition-colors"
                      >
                        {item.description}
                      </button>
                      <Button
                        type="button"
                        variant="soft"
                        size="sm"
                        className="shrink-0 rounded-full"
                        onClick={() => void onRewrite(item)}
                      >
                        <Wrench className="h-3.5 w-3.5" />
                        Fix
                      </Button>
                    </div>
                  </div>
                </li>
              ))
            ) : (
              <li className="text-sm text-text-sub">No flagged clauses yet.</li>
            )}
          </ul>
        </FindingsSection>

        {/* Missing Protections */}
        <FindingsSection
          title="Missing Protections"
          icon={<ShieldAlert size={24} className="text-rose-500" />}
        >
          <ul className="space-y-4">
            {missingItems.length > 0 ? (
              missingItems.map((item) => (
                <li key={item.name} className="flex items-start gap-3 group">
                  <Minus
                    size={16}
                    className="text-slate-300 mt-1 flex-shrink-0 group-hover:text-rose-400 transition-colors"
                  />
                  <span className="text-slate-600 leading-relaxed font-light">
                    <span className="font-medium text-text">{item.name}:</span>{' '}
                    {item.notes ?? 'This protection does not appear in the current contract text.'}
                  </span>
                </li>
              ))
            ) : (
              <li className="text-sm text-text-sub">No missing protections were flagged.</li>
            )}
          </ul>
        </FindingsSection>
      </div>
    </section>
  )
}
