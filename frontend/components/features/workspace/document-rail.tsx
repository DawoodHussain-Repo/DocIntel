'use client'

import { ArrowUpRight, FileSearch, FileText, ScrollText, ShieldAlert, Sparkles } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ClauseNode, ContractType, RiskLevel } from '@/lib/types'
import type { ReviewItem } from '@/lib/analysis-helpers'

interface SectionLink {
  id: string
  label: string
  icon: typeof Sparkles
}

interface DocumentRailProps {
  activeFile: string | null
  contractType?: ContractType
  riskLevel?: RiskLevel
  riskScore?: number
  clauseItems: ClauseNode[]
  flaggedItems: ReviewItem[]
  onJump: (sectionId: string) => void
}

function riskBadgeVariant(level: RiskLevel) {
  if (level === 'red') return 'high'
  if (level === 'yellow') return 'medium'
  return 'low'
}

function dotClass(level: RiskLevel | ReviewItem['tone']) {
  if (level === 'red' || level === 'high') return 'bg-danger'
  if (level === 'yellow' || level === 'medium') return 'bg-warning'
  return 'bg-success'
}

const SECTION_LINKS: SectionLink[] = [
  { id: 'overview', label: 'Overview', icon: Sparkles },
  { id: 'findings', label: 'Good / bad', icon: ShieldAlert },
  { id: 'details', label: 'Key details', icon: FileText },
  { id: 'clauses', label: 'Clause map', icon: ScrollText },
  { id: 'document', label: 'Source document', icon: FileSearch },
]

export function DocumentRail({
  activeFile,
  contractType,
  riskLevel,
  riskScore,
  clauseItems,
  flaggedItems,
  onJump,
}: DocumentRailProps) {
  return (
    <aside className="card sticky top-20 h-fit p-5">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
          <ScrollText className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="label">Document rail</p>
          <p className="truncate text-sm text-text-sub">{activeFile ?? 'No file selected'}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {contractType ? <Badge variant="type">{contractType}</Badge> : null}
        {riskLevel && typeof riskScore === 'number' ? (
          <Badge variant={riskBadgeVariant(riskLevel)}>{riskScore} risk</Badge>
        ) : null}
      </div>

      <div className="mt-6 space-y-1">
        {SECTION_LINKS.map(({ id, label, icon: Icon }) => (
          <Button
            key={id}
            type="button"
            variant="ghost"
            className="w-full justify-between rounded-2xl px-3"
            onClick={() => onJump(id)}
          >
            <span className="flex items-center gap-2">
              <Icon className="h-4 w-4" />
              {label}
            </span>
            <ArrowUpRight className="h-4 w-4" />
          </Button>
        ))}
      </div>

      <div className="hairline my-5" />

      <div>
        <p className="label">Flagged sections</p>
        <div className="mt-3 space-y-2">
          {flaggedItems.length > 0 ? (
            flaggedItems.slice(0, 6).map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onJump(item.id)}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-left transition-colors hover:bg-black/[0.03]"
              >
                <span className={cn('h-2.5 w-2.5 rounded-full', dotClass(item.tone))} />
                <span className="truncate text-sm text-text-sub">{item.title}</span>
              </button>
            ))
          ) : (
            <div className="surface-muted px-4 py-3 text-sm text-text-sub">
              No flagged items yet.
            </div>
          )}
        </div>
      </div>

      <div className="hairline my-5" />

      <div>
        <p className="label">Clause map</p>
        <div className="mt-3 space-y-2">
          {clauseItems.length > 0 ? (
            clauseItems.slice(0, 10).map((clause) => (
              <button
                key={clause.id}
                type="button"
                onClick={() => onJump(`clause-${clause.id}`)}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-left transition-colors hover:bg-black/[0.03]"
              >
                <span className={cn('h-2.5 w-2.5 rounded-full', dotClass(clause.risk_level))} />
                <span className="truncate text-sm text-text-sub">
                  {clause.number ? `${clause.number}. ` : ''}
                  {clause.title}
                </span>
              </button>
            ))
          ) : (
            <div className="surface-muted px-4 py-3 text-sm text-text-sub">
              Clause parsing has not populated yet.
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
