'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { CalendarDays, Download, ShieldCheck } from 'lucide-react'

import { RiskGauge } from '@/components/RiskGauge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useDocumentAnalysis } from '@/hooks/useDocumentAnalysis'
import { BACKEND_URL } from '@/lib/config'

function riskBadgeVariant(level: 'red' | 'yellow' | 'green') {
  if (level === 'red') return 'high'
  if (level === 'yellow') return 'medium'
  return 'low'
}

function ReportContent() {
  const searchParams = useSearchParams()
  const file = searchParams.get('file')
  const { data: analysis, isLoading, error } = useDocumentAnalysis(file)

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <div className="overflow-hidden rounded-3xl border border-border bg-white shadow-card">
        <div className="flex items-center justify-between border-b border-slate-100 px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">DocIntel</p>
              <p className="text-xs text-text-sub">Report Preview</p>
            </div>
          </div>

          {file ? (
            <Button asChild variant="primary">
              <a
                href={`${BACKEND_URL}/api/report_pdf?file=${encodeURIComponent(file)}`}
                target="_blank"
                rel="noreferrer"
              >
                <Download className="h-4 w-4" />
                Download PDF Report
              </a>
            </Button>
          ) : null}
        </div>

        <div className="px-8 py-8">
          {isLoading ? (
            <div className="space-y-6">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-56 w-full" />
            </div>
          ) : error || !analysis ? (
            <div className="rounded-xl border border-danger/20 bg-danger/5 px-5 py-4 text-sm text-danger">
              {error ?? 'Report data is unavailable.'}
            </div>
          ) : (
            <div className="space-y-8">
              <section className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
                <div>
                  <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">{analysis.file}</h1>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-text-sub">
                    <span className="inline-flex items-center gap-2">
                      <CalendarDays className="h-4 w-4" />
                      {new Date().toLocaleDateString()}
                    </span>
                    <Badge variant="type">{analysis.classification.contract_type}</Badge>
                  </div>
                  <p className="mt-4 max-w-2xl text-sm leading-6 text-text-sub">
                    {analysis.classification.rationale}
                  </p>
                </div>

                <div className="flex items-center gap-5">
                  <RiskGauge
                    score={analysis.risk.overall_score}
                    className="h-24 w-24"
                    textClassName="text-slate-900"
                  />
                  <div>
                    <p className="label">
                      Overall risk
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">
                      {analysis.risk.overall_score}
                    </p>
                    <Badge className="mt-2" variant={riskBadgeVariant(analysis.risk.level)}>
                      {analysis.risk.level}
                    </Badge>
                  </div>
                </div>
              </section>

              <section className="rounded-2xl border border-border p-5">
                <h2 className="text-xl font-semibold text-slate-900">AI Summary</h2>
                <div className="mt-4 space-y-3">
                  {analysis.executive_summary.map((bullet) => (
                    <div key={bullet} className="flex gap-3">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                      <p className="text-sm leading-6 text-text-sub">{bullet}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-border p-5">
                <h2 className="text-xl font-semibold text-slate-900">Risk Highlights</h2>
                <div className="mt-4 space-y-3">
                  {analysis.risk.red_flags.map((flag) => (
                    <div key={flag.title} className="rounded-2xl border border-border px-4 py-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-slate-900">{flag.title}</p>
                        <Badge
                          variant={
                            flag.severity === 'high'
                              ? 'high'
                              : flag.severity === 'medium'
                                ? 'medium'
                                : 'low'
                          }
                        >
                          {flag.severity}
                        </Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-text-sub">
                        {flag.description}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-border p-5">
                <h2 className="text-xl font-semibold text-slate-900">Extracted Fields</h2>
                <div className="mt-4 overflow-hidden rounded-xl border border-border">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-text-sub">
                      <tr>
                        <th className="px-4 py-3 font-medium">Field</th>
                        <th className="px-4 py-3 font-medium">Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {analysis.extracted_fields.map((field) => (
                        <tr key={field.key}>
                          <td className="px-4 py-3 font-medium text-slate-900">
                            {field.label}
                          </td>
                          <td className="px-4 py-3 text-text-sub">
                            {field.value ?? (
                              <span className="font-medium text-danger">Not specified</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        @media print {
          header {
            display: none !important;
          }

          body {
            background: #ffffff !important;
          }

          main {
            padding: 0 !important;
          }
        }
      `}</style>
    </main>
  )
}

export default function ReportPage() {
  return (
    <Suspense>
      <ReportContent />
    </Suspense>
  )
}

