export type CardStyle = "cloze_heavy" | "qa_heavy" | "balanced";
export type DeckSize = "small" | "medium" | "large";

export type JobStatus =
  | "pending"
  | "stage_a"
  | "stage_b"
  | "stage_c"
  | "stage_d"
  | "stage_e"
  | "stage_f"
  | "qc"
  | "completed"
  | "failed";

export interface UploadResponse {
  document_id: string;
  filename: string;
  file_type: string;
  section_count: number;
  chunk_count: number;
  word_count: number;
}

export interface GenerateResponse {
  job_id: string;
  status: string;
}

export interface JobStatusResponse {
  job_id: string;
  document_id: string;
  status: JobStatus;
  current_stage: string | null;
  error_message: string | null;
  total_cards: number;
  suppressed_cards: number;
}

export interface CardOut {
  id: string;
  front: string;
  back: string;
  card_type: "cloze" | "basic";
  tags: string | null;
  critique_verdict: "pass" | "rewrite" | "suppress" | null;
  suppressed: boolean;
}

export interface SectionCards {
  section_id: string;
  section_title: string | null;
  cards: CardOut[];
}

export interface ReviewResponse {
  document_id: string;
  title: string | null;
  total_cards: number;
  active_cards: number;
  suppressed_cards: number;
  sections: SectionCards[];
}

export const STAGE_LABELS: Record<string, string> = {
  pending: "Queued",
  stage_a: "Extracting Concepts",
  stage_b: "Merging & Ranking",
  stage_c: "Planning Cards",
  stage_d: "Generating Cards",
  stage_e: "Quality Critique",
  stage_f: "Deduplication",
  qc: "Final QC Check",
  completed: "Complete",
  failed: "Failed",
};

export const STAGE_ORDER: JobStatus[] = [
  "pending",
  "stage_a",
  "stage_b",
  "stage_c",
  "stage_d",
  "stage_e",
  "stage_f",
  "qc",
  "completed",
];
