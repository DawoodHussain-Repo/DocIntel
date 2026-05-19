'use client'

import { FileText } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import type { ClauseNode } from '@/lib/types'

interface ClauseMapPanelProps {
  clauseItems: ClauseNode[]
  setSectionRef: (key: string, node: HTMLDivElement | null) => void
}

function riskBadgeVariant(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'high'
  if (level === 'yellow') return 'medium'
  return 'low'
}

export function ClauseMapPanel({
  clauseItems,
  setSectionRef,
}: ClauseMapPanelProps) {
  if (clauseItems.length === 0) {
    return null
  }

  return (
    <section id="clauses" className="card p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
          <FileText className="h-4 w-4" />
        </div>
        <div>
          <p className="label">Clause map</p>
          <h2 className="mt-2 font-serif text-2xl text-text">Structured contract outline</h2>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {clauseItems.map((clause) => (
          <div
            key={clause.id}
            ref={(node) => setSectionRef(`clause-${clause.id}`, node)}
            className="surface-muted px-5 py-4"
          >
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <p className="label">{clause.number ? `Clause ${clause.number}` : 'Clause'}</p>
                <h3 className="mt-2 text-base font-semibold text-text">{clause.title}</h3>
                <p className="mt-1 text-xs text-text-sub">
                  Pages {clause.page_start}
                  {clause.page_end > clause.page_start ? `–${clause.page_end}` : ''}
                </p>
              </div>
              <Badge variant={riskBadgeVariant(clause.risk_level)}>{clause.risk_level}</Badge>
            </div>

            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-text-sub hover:text-text">
                View clause text
              </summary>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">
                {clause.text}
              </p>
              {clause.children.length > 0 ? (
                <div className="mt-4 space-y-2">
                  {clause.children.map((child) => (
                    <div
                      key={child.id}
                      className="rounded-2xl border border-border bg-white px-4 py-3"
                    >
                      <p className="label">
                        {child.number ? `Subclause ${child.number}` : 'Subclause'}
                      </p>
                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-text">
                        {child.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : null}
            </details>
          </div>
        ))}
      </div>
    </section>
  )
}
