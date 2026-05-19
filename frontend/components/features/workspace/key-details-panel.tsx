'use client'

import { Copy, FolderKanban } from 'lucide-react'

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import type { FieldSection } from '@/lib/analysis-helpers'
import type { ContractType, MissingClause } from '@/lib/types'

interface KeyDetailsPanelProps {
  isLoading: boolean
  fieldSections: FieldSection[]
  missingProtections: MissingClause[]
  contractType?: ContractType
}

export function KeyDetailsPanel({
  isLoading,
  fieldSections,
  missingProtections,
  contractType,
}: KeyDetailsPanelProps) {
  return (
    <section id="details" className="card p-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
            <FolderKanban className="h-4 w-4" />
          </div>
          <div>
            <p className="label">Key details</p>
            <h2 className="mt-2 font-serif text-2xl text-text">Extracted contract data</h2>
          </div>
        </div>
        {contractType ? <Badge variant="type">{contractType}</Badge> : null}
      </div>

      <div className="mt-5">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <Accordion
            type="multiple"
            defaultValue={fieldSections.slice(0, 2).map((section) => section.title)}
          >
            {fieldSections.map((section) => (
              <AccordionItem key={section.title} value={section.title}>
                <AccordionTrigger>{section.title}</AccordionTrigger>
                <AccordionContent>
                  <TooltipProvider>
                    <div className="space-y-2">
                      {section.fields.map((field) => (
                        <div
                          key={field.key}
                          className="surface-muted flex items-start justify-between gap-3 px-4 py-3"
                        >
                          <div className="min-w-0">
                            <p className="label">{field.label}</p>
                            <p
                              className={cn(
                                'mt-2 text-sm leading-6',
                                field.value ? 'text-text' : 'text-danger',
                              )}
                            >
                              {field.value ?? '— Not specified'}
                            </p>
                          </div>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white text-text-sub transition-colors hover:text-text"
                                aria-label={`Copy ${field.label}`}
                                onClick={() => {
                                  if (!field.value) {
                                    return
                                  }
                                  void navigator.clipboard.writeText(field.value)
                                }}
                              >
                                <Copy className="h-4 w-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Copy value</TooltipContent>
                          </Tooltip>
                        </div>
                      ))}
                    </div>
                  </TooltipProvider>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        )}
      </div>

      {missingProtections.length > 0 ? (
        <div className="mt-6">
          <div className="hairline mb-4" />
          <p className="label">Missing protections</p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {missingProtections.map((item) => (
              <div key={item.name} className="surface-muted border-danger/10 bg-danger/[0.03] px-4 py-4">
                <p className="text-sm font-medium text-text">{item.name}</p>
                {item.notes ? (
                  <p className="mt-2 text-sm leading-6 text-text-sub">{item.notes}</p>
                ) : (
                  <p className="mt-2 text-sm leading-6 text-text-sub">
                    This protection does not appear to be specified in the uploaded contract.
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
