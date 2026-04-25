"use client";

import { CheckCircle2, Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface UploadStep {
  key: string;
  label: string;
  status: "pending" | "active" | "complete";
}

function StepRow({ step }: { step: UploadStep }) {
  return (
    <div className="surface-muted flex items-center justify-between gap-3 px-4 py-3">
      <p className="text-sm text-text-sub">{step.label}</p>
      {step.status === "complete" && (
        <CheckCircle2 className="h-5 w-5 text-success" />
      )}
      {step.status === "active" && (
        <Loader2 className="h-5 w-5 animate-spin text-accent" />
      )}
      {step.status === "pending" && (
        <div className="h-5 w-5 rounded-full border border-border bg-white" />
      )}
    </div>
  );
}

export function UploadProgressModal(props: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fileName: string | null;
  steps: UploadStep[];
  statusText: string;
  errorText?: string | null;
}) {
  const { open, onOpenChange, fileName, steps, statusText, errorText } = props;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl border-border bg-white">
        <DialogHeader>
          <DialogTitle>Processing document</DialogTitle>
          <DialogDescription className="text-text-sub">
            {fileName ?? "Preparing upload"}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-5 grid gap-2">
          {steps.map((step) => (
            <StepRow key={step.key} step={step} />
          ))}
        </div>

        <div className="surface-muted mt-4 px-4 py-3">
          <p className="text-sm text-text">{statusText}</p>
          {errorText ? (
            <p className="mt-1 text-sm text-danger">{errorText}</p>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}

