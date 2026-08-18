const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CaseCreatePayload {
  description: string;
  title?: string;
  incident_date?: string;
  location?: string;
  amount?: string;
  parties_involved?: string;
  evidence_available?: string;
  additional_context?: string;
  case_type?: string;
  is_demo?: boolean;
}

export interface Party {
  id: string;
  name: string;
  role: string;
  description?: string;
}

export interface Fact {
  id: string;
  description: string;
  fact_type: string;
  date?: string;
  location?: string;
  amount?: string;
  confidence: string;
}

export interface Case {
  id: string;
  title?: string;
  description: string;
  case_type?: string;
  incident_date?: string;
  location?: string;
  jurisdiction: string;
  is_demo: boolean;
  parties: Party[];
  facts: Fact[];
  created_at: string;
  updated_at: string;
}

export interface CaseSummary {
  id: string;
  title?: string;
  case_type?: string;
  description_preview: string;
  party_count: number;
  fact_count: number;
  created_at: string;
  has_analysis: boolean;
}

export interface MissingInformation {
  id: string;
  question: string;
  why_it_matters: string;
  priority: string;
}

export interface Issue {
  id: string;
  issue: string;
  why_it_matters: string;
  missing_fact_descriptions: string[];
  priority: string;
}

export interface LegalSource {
  id: string;
  title: string;
  source_type: string;
  jurisdiction: string;
  section?: string;
  text: string;
  source_url?: string;
  version?: string;
}

export interface Citation {
  id: string;
  legal_source_id: string;
  claim: string;
  quoted_text?: string;
  is_verified: boolean;
  verification_note?: string;
}

export interface LegalProvision {
  explanation: string;
  applicability: string;
  uncertainty: string;
  counterarguments: string[];
  confidence: string;
  legal_source: LegalSource;
  citations: Citation[];
}

export interface LegalAnalysis {
  issue_id: string;
  summary: string;
  overall_confidence: string;
  provisions: LegalProvision[];
}

export interface Argument {
  position: string;
  strongest_arguments: string[];
  possible_defenses: string[];
  weaknesses: string[];
  confidence: string;
}

export interface Recommendation {
  id: string;
  action: string;
  rationale: string;
  priority: string;
}

export interface Analysis {
  id: string;
  case_id: string;
  status: string;
  summary?: string;
  legal_domains: string[];
  inferred_facts: string[];
  issues: Issue[];
  legal_analyses: LegalAnalysis[];
  claimant_argument?: Argument | null;
  respondent_argument?: Argument | null;
  missing_information: MissingInformation[];
  recommendations: Recommendation[];
  retrieved_sources: LegalSource[];
  overall_confidence: string;
  uncertainty_explanation?: string;
  unsupported_claims: string[];
  disclaimer: string;
  created_at: string;
  completed_at?: string;
}

export interface ChatMessage {
  id: string;
  case_id: string;
  role: string;
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatResponse {
  message: ChatMessage;
  retrieved_sources: LegalSource[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = error.detail;
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/api/v1/health"),

  createCase: (data: CaseCreatePayload) =>
    request<Case>("/api/v1/cases", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listCases: () => request<CaseSummary[]>("/api/v1/cases"),

  getCase: (id: string) => request<Case>(`/api/v1/cases/${id}`),

  analyzeCase: (id: string) =>
    request<Analysis>(`/api/v1/cases/${id}/analyze`, { method: "POST" }),

  getAnalysis: (id: string) => request<Analysis>(`/api/v1/cases/${id}/analysis`),

  getCaseSources: (id: string) => request<LegalSource[]>(`/api/v1/cases/${id}/sources`),

  listMessages: (id: string) => request<ChatMessage[]>(`/api/v1/cases/${id}/messages`),

  sendMessage: (id: string, message: string) =>
    request<ChatResponse>(`/api/v1/cases/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  searchLegal: (query: string) =>
    request<LegalSource[]>("/api/v1/legal/search", {
      method: "POST",
      body: JSON.stringify({ query, limit: 10 }),
    }),

  listSources: () => request<LegalSource[]>("/api/v1/legal/sources"),
};
