export type MessageRole = "user" | "assistant";

export interface UploadContractData {
  file: string;
  chunks_indexed: number;
  collection: string;
}

export interface SuccessResponse<TData> {
  status: "success";
  data: TData;
  message?: string | null;
}

export interface ErrorResponse {
  status: "error";
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
}

export interface ToolCallEvent {
  tool: string;
  query: string;
}

export interface TokenEvent {
  text: string;
}

export interface DoneEvent {
  finish_reason: "stop" | "error" | "timeout";
  error: string | null;
  run_id?: string;
}

export interface StreamHandlers {
  onToolCall: (event: ToolCallEvent) => void;
  onToken: (event: TokenEvent) => void;
  onDone: (event: DoneEvent) => void;
}

export interface EvidenceSnippet {
  page_number: number;
  heading: string;
  snippet: string;
}

export type ContractType = "NDA" | "Lease" | "Freelance Agreement" | "Other";

export interface ContractClassification {
  contract_type: ContractType;
  confidence: number;
  rationale: string;
  evidence: EvidenceSnippet[];
}

export interface ExtractedFieldValue {
  key: string;
  label: string;
  value: string | null;
  confidence: number;
  evidence: EvidenceSnippet[];
  notes: string | null;
}

export type RiskLevel = "green" | "yellow" | "red";
export type RiskSeverity = "low" | "medium" | "high";

export interface RiskFlag {
  title: string;
  severity: RiskSeverity;
  score_impact: number;
  description: string;
  evidence: EvidenceSnippet[];
}

export interface RiskReport {
  overall_score: number;
  level: RiskLevel;
  rationale: string;
  red_flags: RiskFlag[];
  recommendations: string[];
}

export interface MissingClause {
  name: string;
  present: boolean;
  notes: string | null;
  evidence: EvidenceSnippet[];
}

export interface ClauseNode {
  id: string;
  number: string | null;
  title: string;
  text: string;
  page_start: number;
  page_end: number;
  risk_level: RiskLevel;
  children: ClauseNode[];
}

export interface DocumentAnalysisData {
  file: string;
  executive_summary: string[];
  classification: ContractClassification;
  extracted_fields: ExtractedFieldValue[];
  risk: RiskReport;
  missing_clauses: MissingClause[];
  clauses: ClauseNode[];
}

export interface RewriteClauseData {
  replacement_clause: string;
  rationale: string;
  negotiation_notes: string[];
  confidence: number;
}
