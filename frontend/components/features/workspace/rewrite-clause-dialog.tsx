'use client'

import { Copy } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'

interface RewriteClauseDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  original: string
  replacement: string
  rationale: string
  isLoading: boolean
}

export function RewriteClauseDialog({
  open,
  onOpenChange,
  title,
  original,
  replacement,
  rationale,
  isLoading,
}: RewriteClauseDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl border-border bg-white">
        <DialogHeader>
          <DialogTitle>{title || 'Rewrite clause'}</DialogTitle>
          <DialogDescription className="text-text-sub">
            The original evidence snippet is on the left. The live backend rewrite is on the right.
          </DialogDescription>
        </DialogHeader>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <div className="rounded-[22px] border border-danger/20 bg-danger/[0.04] p-5">
            <p className="label text-danger">Original</p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">{original}</p>
          </div>
          <div className="rounded-[22px] border border-success/20 bg-success/[0.04] p-5">
            <p className="label text-success">Suggested replacement</p>
            {isLoading ? (
              <Skeleton className="mt-3 h-36 w-full" />
            ) : (
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">
                {replacement}
              </p>
            )}
          </div>
        </div>

        {rationale ? (
          <div className="surface-muted mt-4 px-4 py-4">
            <p className="label">Rationale</p>
            <p className="mt-2 text-sm leading-6 text-text-sub">{rationale}</p>
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            variant="primary"
            onClick={() => void navigator.clipboard.writeText(replacement)}
            disabled={!replacement}
          >
            <Copy className="h-4 w-4" />
            Copy suggestion
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
