'use client'

import Link from 'next/link'
import { ArrowUpRight, FileSearch, RefreshCcw, Download, ScanText, ShieldCheck, Sparkles } from 'lucide-react'

import { RiskGauge } from '@/components/RiskGauge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { BACKEND_URL } from '@/lib/config'
import type { DocumentAnalysisData } from '@/lib/types'

interface AnalysisHeroProps {
  activeFile: string | null
  analysis: DocumentAnalysisData | null
  isLoading: boolean
  error: string | null
}

function riskBadgeVariant(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'high'
  if (level === 'yellow') return 'medium'
  return 'low'
}

function riskColorClass(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'text-rose-500'
  if (level === 'yellow') return 'text-amber-500'
  return 'text-emerald-500'
}

function riskDotClass(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'bg-rose-500'
  if (level === 'yellow') return 'bg-amber-500'
  return 'bg-emerald-500'
}

function riskLabel(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'High Risk'
  if (level === 'yellow') return 'Medium Risk'
  return 'Low Risk'
}

export function AnalysisHero({
  activeFile,
  analysis,
  isLoading,
  error,
}: AnalysisHeroProps) {
  const flaggedCount = analysis?.risk.red_flags.length ?? 0
  const missingCount = analysis?.missing_clauses.filter((item) => !item.present).length ?? 0
  const extractedCount = analysis?.extracted_fields.length ?? 0

  return (
    <section id="overview" className="overflow-hidden rounded-3xl border border-border bg-white shadow-card">
      {/* Header */}
      <div className="border-b border-slate-100 p-10 pb-8">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={16} className="text-accent" />
              <h2 className="text-xs font-bold tracking-widest text-accent uppercase">
                AI Document Analysis
              </h2>
            </div>
            <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">
              {activeFile ?? 'No document selected'}
            </h1>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {analysis?.classification ? (
                <Badge variant="type">{analysis.classification.contract_type}</Badge>
              ) : null}
              {analysis?.risk ? (
                <Badge variant={riskBadgeVariant(analysis.risk.level)}>
                  {analysis.risk.level}
                </Badge>
              ) : null}
              <p className="text-sm text-text-sub">
                Plain-English analysis grounded in your upload
              </p>
            </div>
          </div>
          <div className="flex gap-3 shrink-0">
            {activeFile ? (
              <>
                <Button asChild variant="ghost" className="rounded-xl">
                  <Link href={`/report?file=${encodeURIComponent(activeFile)}`}>
                    <ScanText className="h-4 w-4" />
                    Report
                  </Link>
                </Button>
                <Button asChild variant="primary" className="rounded-xl">
                  <a
                    href={`${BACKEND_URL}/api/report_pdf?file=${encodeURIComponent(activeFile)}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Download size={16} />
                    Export
                  </a>
                </Button>
              </>
            ) : null}
          </div>
        </div>
      </div>

      {/* Hero Metric & Summary */}
      <div className="border-b border-slate-100 bg-slate-50/50 p-10">
        <div className="flex flex-col gap-12 md:flex-row md:items-center">
          {/* Primary Metric */}
          {analysis?.risk ? (
            <>
              <div className="flex flex-col items-center justify-center min-w-[180px]">
                <div className={`text-7xl font-light tracking-tighter ${riskColorClass(analysis.risk.level)} mb-2`}>
                  {analysis.risk.overall_score}
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${riskDotClass(analysis.risk.level)}`} />
                  <span className="text-sm font-bold text-slate-700 uppercase tracking-widest">
                    {riskLabel(analysis.risk.level)}
                  </span>
                </div>
              </div>

              {/* Divider */}
              <div className="hidden md:block w-px h-32 bg-slate-200" />
            </>
          ) : null}

          {/* Executive Summary */}
          <div className="flex-1 space-y-4">
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-[92%]" />
                <Skeleton className="h-5 w-[88%]" />
              </div>
            ) : analysis ? (
              <div className="text-slate-600 text-lg leading-relaxed font-light space-y-3">
                {analysis.executive_summary.map((bullet) => (
                  <p key={bullet}>{bullet}</p>
                ))}
              </div>
            ) : (
              <p className="text-sm text-danger">{error ?? 'Analysis unavailable.'}</p>
            )}
          </div>
        </div>
      </div>

      {/* Secondary Metrics Row */}
      <div className="border-b border-slate-100 px-10 py-8">
        <div className="grid grid-cols-3 gap-8">
          <div className="flex flex-col">
            <div className="text-4xl font-light tracking-tight text-slate-900 mb-2">
              {String(extractedCount).padStart(2, '0')}
            </div>
            <div className="text-xs font-bold tracking-wider text-slate-500 uppercase">
              Fields Extracted
            </div>
          </div>
          <div className="flex flex-col">
            <div className="text-4xl font-light tracking-tight text-rose-600 mb-2">
              {String(flaggedCount).padStart(2, '0')}
            </div>
            <div className="text-xs font-bold tracking-wider text-slate-500 uppercase">
              Risk Flags
            </div>
          </div>
          <div className="flex flex-col">
            <div className="text-4xl font-light tracking-tight text-amber-600 mb-2">
              {String(missingCount).padStart(2, '0')}
            </div>
            <div className="text-xs font-bold tracking-wider text-slate-500 uppercase">
              Missing Protections
            </div>
          </div>
        </div>
      </div>

      {/* Risk Rationale */}
      <div className="p-10">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(260px,0.9fr)]">
          <div>
            <div className="flex items-center gap-2 text-text">
              <ShieldCheck className="h-4 w-4 text-success" />
              <p className="label">Risk Rationale</p>
            </div>
            <p className="mt-4 text-sm leading-6 text-text-sub">
              {analysis?.risk.rationale ??
                'Upload a document to see the overall risk rationale and scoring explanation.'}
            </p>
          </div>

          <div className="surface-muted flex items-center gap-5 px-5 py-5">
            <RiskGauge score={analysis?.risk.overall_score ?? 0} />
            <div>
              <p className="label">Overall risk score</p>
              <p className="mt-2 text-3xl font-semibold text-text">
                {analysis?.risk.overall_score ?? '--'}
              </p>
              {analysis?.risk ? (
                <Badge className="mt-2" variant={riskBadgeVariant(analysis.risk.level)}>
                  {analysis.risk.level}
                </Badge>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
