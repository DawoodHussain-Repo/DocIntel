import {
  DocumentAnalysisData,
  EvidenceSnippet,
  ExtractedFieldValue,
  MissingClause,
  RiskFlag,
} from "@/lib/types";

export type InsightTone = "high" | "medium" | "low";

export interface ReviewItem {
  id: string;
  title: string;
  tone: InsightTone;
  description: string;
  evidence: EvidenceSnippet[];
  kind: "risk" | "missing";
}

export interface FieldSection {
  title: string;
  fields: ExtractedFieldValue[];
}

const SECTION_TITLES = [
  "Parties",
  "Dates & Deadlines",
  "Financial Terms",
  "Jurisdiction",
  "Termination",
  "IP Rights",
  "Confidentiality",
] as const;

type SectionTitle = (typeof SECTION_TITLES)[number];

function getSectionForField(field: ExtractedFieldValue): SectionTitle {
  const key = field.key.toLowerCase();
  const label = field.label.toLowerCase();

  if (key.includes("party") || label.includes("party")) {
    return "Parties";
  }

  if (
    key.includes("date") ||
    key.includes("renewal") ||
    key.includes("term") ||
    label.includes("date") ||
    label.includes("term")
  ) {
    return "Dates & Deadlines";
  }

  if (
    key.includes("payment") ||
    key.includes("fee") ||
    key.includes("currency") ||
    label.includes("payment") ||
    label.includes("fee")
  ) {
    return "Financial Terms";
  }

  if (
    key.includes("governing_law") ||
    key.includes("jurisdiction") ||
    key.includes("arbitration") ||
    label.includes("jurisdiction") ||
    label.includes("law") ||
    label.includes("arbitration")
  ) {
    return "Jurisdiction";
  }

  if (key.includes("termination") || label.includes("termination") || key.includes("notice")) {
    return "Termination";
  }

  if (
    key.includes("ip") ||
    key.includes("license") ||
    key.includes("assignment") ||
    label.includes("ip") ||
    label.includes("license")
  ) {
    return "IP Rights";
  }

  return "Confidentiality";
}

function toReviewItemFromFlag(flag: RiskFlag, index: number): ReviewItem {
  return {
    id: `risk-${index}`,
    title: flag.title,
    tone: flag.severity,
    description: flag.description,
    evidence: flag.evidence,
    kind: "risk",
  };
}

function toReviewItemFromMissingClause(item: MissingClause, index: number): ReviewItem {
  return {
    id: `missing-${index}`,
    title: item.name,
    tone: "medium",
    description: item.notes ?? "This protection does not appear to be specified in the uploaded document.",
    evidence: item.evidence,
    kind: "missing",
  };
}

export function buildReviewItems(analysis: DocumentAnalysisData): ReviewItem[] {
  const riskItems = analysis.risk.red_flags.map(toReviewItemFromFlag);
  const missingItems = analysis.missing_clauses
    .filter((item) => !item.present)
    .map(toReviewItemFromMissingClause);

  return [...riskItems, ...missingItems];
}

export function groupExtractedFields(analysis: DocumentAnalysisData): FieldSection[] {
  const bySection = new Map<SectionTitle, ExtractedFieldValue[]>();

  SECTION_TITLES.forEach((title) => bySection.set(title, []));

  analysis.extracted_fields.forEach((field) => {
    const title = getSectionForField(field);
    bySection.get(title)?.push(field);
  });

  return SECTION_TITLES.map((title) => ({
    title,
    fields: bySection.get(title) ?? [],
  })).filter((section) => section.fields.length > 0);
}

