"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertCircle,
  ArrowUpRight,
  Bot,
  Copy,
  FileText,
  FileSearch,
  FileWarning,
  FolderKanban,
  MessageSquareText,
  ScanText,
  ScrollText,
  Sparkles,
  UserRound,
  Wrench,
} from "lucide-react";

import { RiskGauge } from "@/components/RiskGauge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { buildReviewItems, groupExtractedFields, type ReviewItem } from "@/lib/analysis-helpers";
import { BACKEND_URL, MAX_QUERY_LENGTH, QUERY_WARNING_THRESHOLD } from "@/lib/config";
import { getRecentDocuments } from "@/lib/file-store";
import { cn } from "@/lib/utils";
import { useClauseRewrite } from "@/hooks/useClauseRewrite";
import { useChatStream } from "@/hooks/useChatStream";
import { useDocumentAnalysis } from "@/hooks/useDocumentAnalysis";
import { useDocumentPreview } from "@/hooks/useDocumentPreview";
import { useThreadId } from "@/hooks/useThreadId";

function riskBadgeVariant(level: "red" | "yellow" | "green") {
  if (level === "red") return "high";
  if (level === "yellow") return "medium";
  return "low";
}

function reviewToneVariant(tone: ReviewItem["tone"]) {
  if (tone === "high") return "high";
  if (tone === "medium") return "medium";
  return "low";
}

export default function WorkspacePage() {
  const searchParams = useSearchParams();
  const requestedFile = searchParams.get("file");
  const fallbackFile = getRecentDocuments()[0]?.file ?? null;
  const activeFile = requestedFile ?? fallbackFile;

  const { data: analysis, isLoading, error: analysisError } = useDocumentAnalysis(activeFile);
  const {
    data: pdfPreviewUrl,
    status: previewState,
  } = useDocumentPreview(activeFile);

  const [rewriteOpen, setRewriteOpen] = useState(false);
  const [rewriteTitle, setRewriteTitle] = useState("");
  const [rewriteOriginal, setRewriteOriginal] = useState("");
  const [rewriteReplacement, setRewriteReplacement] = useState("");
  const [rewriteReason, setRewriteReason] = useState("");
  const {
    isLoading: isRewriting,
    rewrite,
    reset: resetRewrite,
  } = useClauseRewrite(activeFile);

  const threadId = useThreadId();
  const {
    messages,
    isStreaming,
    streamError,
    currentToolCall,
    sendMessage,
    clearConversation,
  } = useChatStream(threadId, activeFile);
  const [draftMessage, setDraftMessage] = useState("");

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const reviewItems = analysis ? buildReviewItems(analysis) : [];
  const clauseItems = analysis?.clauses ?? [];
  const fieldSections = analysis ? groupExtractedFields(analysis) : [];
  const missingProtections =
    analysis?.missing_clauses.filter((item) => !item.present) ?? [];

  const openRewriteModal = async (item: ReviewItem) => {
    if (!activeFile) {
      return;
    }

    const evidenceText =
      item.evidence.map((snippet) => snippet.snippet).join("\n\n") || item.description;

    setRewriteTitle(item.title);
    setRewriteOriginal(evidenceText);
    setRewriteReplacement("");
    setRewriteReason("");
    resetRewrite();
    setRewriteOpen(true);

    const response = await rewrite(evidenceText, null);
    if (response) {
      setRewriteReplacement(response.replacement_clause);
      setRewriteReason(response.rationale);
      return;
    }

    setRewriteReplacement("Failed to generate a rewrite.");
    setRewriteReason("");
  };

  const scrollToSection = (key: string) => {
    const element = sectionRefs.current[key];
    if (!element) {
      return;
    }

    element.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleSendMessage = async () => {
    const nextMessage = draftMessage.trim();
    if (!nextMessage || !activeFile || nextMessage.length > MAX_QUERY_LENGTH) {
      return;
    }
    setDraftMessage("");
    await sendMessage(nextMessage);
  };

  const queryLength = draftMessage.trim().length;
  const queryTooLong = queryLength > MAX_QUERY_LENGTH;

  return (
    <TooltipProvider>
      <main className="mx-auto max-w-[1400px] px-6 py-6">
        <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
          <motion.aside
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="card sticky top-20 h-[calc(100vh-6.5rem)] overflow-auto p-5"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
                <ScrollText className="h-4 w-4" />
              </div>
              <div>
                <p className="label">Navigator</p>
                <p className="text-sm text-text-sub">Evidence map</p>
              </div>
            </div>
            <h1 className="mt-3 font-serif text-2xl leading-tight">
              {activeFile ?? "No document selected"}
            </h1>

            <div className="mt-4 flex flex-wrap gap-2">
              {analysis?.classification ? (
                <Badge variant="type">{analysis.classification.contract_type}</Badge>
              ) : null}
              {analysis?.risk ? (
                <Badge variant={riskBadgeVariant(analysis.risk.level)}>
                  {analysis.risk.overall_score}
                </Badge>
              ) : null}
            </div>

            <div className="hairline mt-6" />

            <nav className="mt-5 space-y-2">
              <button
                type="button"
                onClick={() => scrollToSection("overview")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-text-sub transition-colors hover:bg-slate-50 hover:text-text"
              >
                <span>Overview</span>
                <ArrowUpRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => scrollToSection("document")}
                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-text-sub transition-colors hover:bg-slate-50 hover:text-text"
              >
                <span>PDF Preview</span>
                <FileSearch className="h-4 w-4" />
              </button>

              {clauseItems.map((clause) => (
                <button
                  key={clause.id}
                  type="button"
                  onClick={() => scrollToSection(`clause-${clause.id}`)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm text-text-sub transition-colors hover:bg-slate-50 hover:text-text"
                >
                  <span className="truncate">
                    {clause.number ? `${clause.number}. ` : ""}
                    {clause.title}
                  </span>
                  <span
                    className={cn(
                      "h-2.5 w-2.5 shrink-0 rounded-full",
                      clause.risk_level === "red"
                        ? "bg-danger"
                        : clause.risk_level === "yellow"
                          ? "bg-warning"
                          : "bg-success",
                    )}
                  />
                </button>
              ))}

              {reviewItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => scrollToSection(item.id)}
                  className="flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm text-text-sub transition-colors hover:bg-slate-50 hover:text-text"
                >
                  <span className="truncate">{item.title}</span>
                  <span
                    className={cn(
                      "h-2.5 w-2.5 shrink-0 rounded-full",
                      item.tone === "high"
                        ? "bg-danger"
                        : item.tone === "medium"
                          ? "bg-warning"
                          : "bg-success",
                    )}
                  />
                </button>
              ))}
            </nav>

            <div className="surface-muted mt-6 px-4 py-4">
              <p className="label">Workspace notes</p>
              <p className="mt-2 text-sm leading-6 text-text-sub">
                Clause evidence comes from the backend analysis response. The original
                PDF preview is restored from the browser cache when available.
              </p>
            </div>
          </motion.aside>

          <section className="space-y-6">
            <motion.div
              ref={(node) => { sectionRefs.current.overview = node; }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.05, ease: "easeOut" }}
              className="card card-hover p-6"
            >
              <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/[0.08] text-accent">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="label">Plain English Summary</p>
                      <p className="text-sm text-text-sub">Live backend analysis</p>
                    </div>
                  </div>
                  <h2 className="mt-3 font-serif text-3xl leading-tight">
                    Contract snapshot
                  </h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-text-sub">
                    Real backend analysis for the selected document, grounded by the
                    current upload index.
                  </p>

                  <div className="mt-5 space-y-3">
                    {isLoading ? (
                      <>
                        <Skeleton className="h-5 w-full" />
                        <Skeleton className="h-5 w-[92%]" />
                        <Skeleton className="h-5 w-[88%]" />
                      </>
                    ) : analysis ? (
                      analysis.executive_summary.map((bullet, index) => (
                        <div key={`${bullet}-${index}`} className="flex gap-3">
                          <span className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                          <p className="text-sm leading-6 text-text-sub">{bullet}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-danger">{analysisError}</p>
                    )}
                  </div>
                </div>

                <div className="surface-muted flex shrink-0 items-center gap-5 px-5 py-4">
                  <RiskGauge score={analysis?.risk.overall_score ?? 0} />
                  <div>
                    <p className="label">Overall risk score</p>
                    <p className="mt-2 text-2xl font-semibold text-text">
                      {analysis?.risk.overall_score ?? "--"}
                    </p>
                    {analysis?.risk ? (
                      <Badge className="mt-2" variant={riskBadgeVariant(analysis.risk.level)}>
                        {analysis.risk.level}
                      </Badge>
                    ) : null}
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              ref={(node) => { sectionRefs.current.document = node; }}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.1, ease: "easeOut" }}
              className="card overflow-hidden"
            >
              <div className="hairline flex items-center justify-between px-6 py-4">
                <div>
                  <p className="label">Document Viewer</p>
                  <h3 className="mt-2 font-serif text-2xl">Original PDF</h3>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {activeFile ? (
                    <Button asChild variant="ghost">
                      <Link href={`/report?file=${encodeURIComponent(activeFile)}`}>
                        <ScanText className="h-4 w-4" />
                        Report preview
                      </Link>
                    </Button>
                  ) : null}
                  {activeFile ? (
                    <Button asChild variant="primary">
                      <a
                        href={`${BACKEND_URL}/api/report_pdf?file=${encodeURIComponent(activeFile)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                        Download report
                      </a>
                    </Button>
                  ) : null}
                </div>
              </div>

              <div className="p-6">
                {previewState === "ready" && pdfPreviewUrl ? (
                  <iframe
                    title="Uploaded PDF preview"
                    src={pdfPreviewUrl}
                    className="h-[720px] w-full rounded-lg border border-border bg-white"
                  />
                ) : previewState === "loading" ? (
                  <Skeleton className="h-[720px] w-full rounded-lg" />
                ) : previewState === "unsupported" ? (
                  <div className="surface-muted flex h-[320px] flex-col items-center justify-center px-8 text-center">
                    <FileSearch className="h-8 w-8 text-text-sub" />
                    <p className="mt-4 text-sm font-medium text-text">
                      In-app preview is currently PDF only
                    </p>
                    <p className="mt-2 max-w-md text-sm leading-6 text-text-sub">
                      The backend analysis is available for this DOCX upload, but the
                      embedded viewer is reserved for PDFs in the current MVP pass.
                    </p>
                  </div>
                ) : (
                  <div className="surface-muted flex h-[320px] flex-col items-center justify-center px-8 text-center">
                    <FileWarning className="h-8 w-8 text-text-sub" />
                    <p className="mt-4 text-sm font-medium text-text">
                      PDF preview unavailable in this session
                    </p>
                    <p className="mt-2 max-w-md text-sm leading-6 text-text-sub">
                      The analysis is still available, but the original file is not cached
                      locally anymore. Upload the PDF again to restore in-app preview.
                    </p>
                  </div>
                )}
              </div>
            </motion.div>

            {clauseItems.length > 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.12, ease: "easeOut" }}
                className="card p-6"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="label">Clause index</p>
                    <h3 className="mt-2 font-serif text-2xl">Structured contract map</h3>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  {clauseItems.map((clause) => (
                    <div
                      key={clause.id}
                      ref={(node) => { sectionRefs.current[`clause-${clause.id}`] = node; }}
                      className="surface-muted px-5 py-4"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <p className="label">
                            {clause.number ? `Clause ${clause.number}` : "Clause"}
                          </p>
                          <h4 className="mt-2 text-base font-semibold text-text">
                            {clause.title}
                          </h4>
                          <p className="mt-1 text-xs text-text-sub">
                            Pages {clause.page_start}
                            {clause.page_end > clause.page_start ? `–${clause.page_end}` : ""}
                          </p>
                        </div>
                        <Badge variant={riskBadgeVariant(clause.risk_level)}>
                          {clause.risk_level}
                        </Badge>
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
                              <div key={child.id} className="rounded-2xl border border-border bg-white px-4 py-3">
                                <p className="label">
                                  {child.number ? `Subclause ${child.number}` : "Subclause"}
                                </p>
                                <p className="mt-2 text-sm leading-6 text-text">{child.text}</p>
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </details>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : null}

            {reviewItems.map((item, index) => (
              <motion.div
                key={item.id}
                ref={(node) => { sectionRefs.current[item.id] = node; }}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.28, delay: 0.16 + index * 0.08, ease: "easeOut" }}
                className="card card-hover p-6"
              >
                <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={reviewToneVariant(item.tone)}>
                        {item.kind === "risk" ? "Review" : "Missing protection"}
                      </Badge>
                      <p className="label">Evidence-backed</p>
                    </div>
                    <h3 className="mt-3 font-serif text-2xl">{item.title}</h3>
                    <p className="mt-3 max-w-2xl text-sm leading-6 text-text-sub">
                      {item.description}
                    </p>

                    <div className="mt-5 space-y-3">
                      {item.evidence.length > 0 ? (
                        item.evidence.map((snippet, index) => (
                          <div key={`${item.id}-${index}`} className="surface-muted px-4 py-4">
                            <div className="flex items-center gap-2">
                              <Badge variant="neutral">Page {snippet.page_number}</Badge>
                              <span className="text-xs text-text-sub">{snippet.heading}</span>
                            </div>
                            <p className="mt-3 text-sm leading-6 text-text">
                              {snippet.snippet}
                            </p>
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
                    <Button variant="primary" onClick={() => void openRewriteModal(item)}>
                      <Wrench className="h-4 w-4" />
                      Fix This
                    </Button>
                  </div>
                </div>
              </motion.div>
            ))}
          </section>

          <motion.aside
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="space-y-6"
          >
            <div className="card p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm">
                    <FolderKanban className="h-4 w-4" />
                  </div>
                  <div>
                  <p className="label">Key Details</p>
                  <h2 className="mt-2 font-serif text-2xl">Extracted fields</h2>
                  </div>
                </div>
                {analysis?.classification ? (
                  <Badge variant="type">{analysis.classification.contract_type}</Badge>
                ) : null}
              </div>

              <div className="mt-5">
                {isLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-28 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-24 w-full" />
                  </div>
                ) : (
                  <Accordion type="multiple" defaultValue={fieldSections.slice(0, 2).map((section) => section.title)}>
                    {fieldSections.map((section) => (
                      <AccordionItem key={section.title} value={section.title}>
                        <AccordionTrigger>{section.title}</AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-2">
                            {section.fields.map((field) => (
                              <div
                                key={field.key}
                                className="surface-muted flex items-start justify-between gap-3 px-4 py-3"
                              >
                                <div>
                                  <p className="label">{field.label}</p>
                                  <p
                                    className={cn(
                                      "mt-2 text-sm leading-6",
                                      field.value ? "text-text" : "text-danger",
                                    )}
                                  >
                                    {field.value ?? "Not specified"}
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
                                          return;
                                        }
                                        void navigator.clipboard.writeText(field.value);
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
                  <div className="mt-3 space-y-2">
                    {missingProtections.map((item) => (
                      <div key={item.name} className="surface-muted px-4 py-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-medium text-text">{item.name}</p>
                          <Badge variant="medium">Missing</Badge>
                        </div>
                        {item.notes ? (
                          <p className="mt-2 text-sm leading-6 text-text-sub">
                            {item.notes}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="card flex h-[calc(100vh-33rem)] min-h-[420px] flex-col p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="label">Ask the Lawyer</p>
                  <h2 className="mt-2 font-serif text-2xl">Document chat</h2>
                </div>
                <MessageSquareText className="h-5 w-5 text-accent" />
              </div>

              <div className="mt-5 flex-1 space-y-3 overflow-auto pr-1">
                {messages.length === 0 ? (
                  <div className="surface-muted px-4 py-4 text-sm text-text-sub">
                    Ask a question about the uploaded document and the backend will answer from the indexed clauses.
                  </div>
                ) : (
                  <AnimatePresence initial={false}>
                    {messages.map((message) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.2, ease: "easeOut" }}
                        className={cn(
                          "flex gap-3",
                          message.role === "user" ? "justify-end" : "justify-start",
                        )}
                      >
                        {message.role === "assistant" ? (
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white">
                            <Bot className="h-4 w-4" />
                          </div>
                        ) : null}
                        <div
                          className={cn(
                            "max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm",
                            message.role === "assistant"
                              ? "bg-slate-900 text-white"
                              : "border border-border bg-white text-text",
                          )}
                        >
                          {message.content}
                        </div>
                        {message.role === "user" ? (
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-white text-text">
                            <UserRound className="h-4 w-4" />
                          </div>
                        ) : null}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                )}
              </div>

              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap gap-2">
                  {[
                    "What are the payment terms?",
                    "Can the agreement be terminated early?",
                    "What happens to the IP?",
                  ].map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => setDraftMessage(question)}
                      className="rounded-full border border-border bg-white px-3 py-1.5 text-xs text-text-sub transition-colors hover:border-slate-300 hover:text-text"
                    >
                      {question}
                    </button>
                  ))}
                </div>

                <AnimatePresence>
                  {currentToolCall ? (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.18 }}
                      className="surface-muted px-3 py-2 text-xs text-text-sub"
                    >
                      Searching: {currentToolCall.tool}
                    </motion.div>
                  ) : null}
                </AnimatePresence>

                {streamError ? (
                  <div className="rounded-lg border border-danger/20 bg-danger/5 px-3 py-2 text-sm text-danger">
                    {streamError}
                  </div>
                ) : null}

                <Textarea
                  value={draftMessage}
                  onChange={(event) => setDraftMessage(event.target.value)}
                  placeholder="Ask anything about this contract..."
                  className="min-h-[108px] bg-white"
                  disabled={!activeFile || isStreaming}
                />

                <div className="flex items-center justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-xs leading-5 text-text-sub">
                      Answers are based strictly on the uploaded document.
                    </p>
                    <p
                      className={cn(
                        "text-xs",
                        queryTooLong
                          ? "text-danger"
                          : queryLength >= QUERY_WARNING_THRESHOLD
                            ? "text-warning"
                            : "text-text-sub",
                      )}
                    >
                      {queryLength}/{MAX_QUERY_LENGTH}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" onClick={clearConversation}>
                      Clear
                    </Button>
                    <Button
                      variant="primary"
                      onClick={() => void handleSendMessage()}
                      disabled={!draftMessage.trim() || !activeFile || isStreaming || queryTooLong}
                    >
                      <Sparkles className="h-4 w-4" />
                      {isStreaming ? "Answering" : "Send"}
                    </Button>
                  </div>
                </div>
                {queryTooLong ? (
                  <div className="mt-2 flex items-center gap-2 rounded-lg border border-danger/20 bg-danger/5 px-3 py-2 text-xs text-danger">
                    <AlertCircle className="h-4 w-4" />
                    Keep the question under {MAX_QUERY_LENGTH} characters.
                  </div>
                ) : null}
              </div>
            </div>
          </motion.aside>
        </div>

        <Dialog open={rewriteOpen} onOpenChange={setRewriteOpen}>
          <DialogContent className="max-w-5xl border-border bg-white">
            <DialogHeader>
              <DialogTitle>{rewriteTitle || "Rewrite clause"}</DialogTitle>
              <DialogDescription className="text-text-sub">
                The original evidence snippet is on the left. The live backend rewrite is on the right.
              </DialogDescription>
            </DialogHeader>

            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-danger/20 bg-danger/[0.04] p-5">
                <p className="label text-danger">Original</p>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">
                  {rewriteOriginal}
                </p>
              </div>
              <div className="rounded-lg border border-success/20 bg-success/[0.04] p-5">
                <p className="label text-success">Suggested replacement</p>
                {isRewriting ? (
                  <Skeleton className="mt-3 h-36 w-full" />
                ) : (
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">
                    {rewriteReplacement}
                  </p>
                )}
              </div>
            </div>

            {rewriteReason ? (
              <div className="surface-muted mt-4 px-4 py-4">
                <p className="label">Rationale</p>
                <p className="mt-2 text-sm leading-6 text-text-sub">{rewriteReason}</p>
              </div>
            ) : null}

            <DialogFooter>
              <Button variant="ghost" onClick={() => setRewriteOpen(false)}>
                Close
              </Button>
              <Button
                variant="primary"
                onClick={() => void navigator.clipboard.writeText(rewriteReplacement)}
                disabled={!rewriteReplacement}
              >
                <Copy className="h-4 w-4" />
                Copy suggestion
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </main>
    </TooltipProvider>
  );
}
