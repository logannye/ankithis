import { getToken } from "./auth";
import type {
  UploadResponse,
  GenerateResponse,
  JobStatusResponse,
  ReviewResponse,
  CardStyle,
  DeckSize,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(): Record<string, string> {
  const token = getToken();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    ...authHeaders(),
    ...Object.fromEntries(
      new Headers(init?.headers).entries(),
    ),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}

export async function register(
  email: string,
  password: string,
  display_name?: string,
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Registration failed`);
  }
  return res.json();
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Login failed`);
  }
  return res.json();
}

export async function uploadDocument(
  file: File,
  options: {
    study_goal?: string;
    card_style?: CardStyle;
    deck_size?: DeckSize;
    scope?: string;
  } = {},
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (options.study_goal) formData.append("study_goal", options.study_goal);
  if (options.card_style) formData.append("card_style", options.card_style);
  if (options.deck_size) formData.append("deck_size", options.deck_size);
  if (options.scope) formData.append("scope", options.scope);

  return apiFetch<UploadResponse>("/api/upload", {
    method: "POST",
    body: formData,
  });
}

export async function generateCards(
  documentId: string,
): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>(
    `/api/documents/${documentId}/generate`,
    { method: "POST" },
  );
}

export async function regenerateCards(
  documentId: string,
): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>(
    `/api/documents/${documentId}/regenerate`,
    { method: "POST" },
  );
}

export async function getJobStatus(
  jobId: string,
): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/api/jobs/${jobId}`);
}

export async function getReview(
  documentId: string,
): Promise<ReviewResponse> {
  return apiFetch<ReviewResponse>(`/api/documents/${documentId}/review`);
}

export async function removeCard(cardId: string): Promise<void> {
  await apiFetch(`/api/cards/${cardId}/remove`, { method: "POST" });
}

export async function removeSectionFromDeck(
  sectionId: string,
): Promise<void> {
  await apiFetch(`/api/sections/${sectionId}/remove-from-deck`, {
    method: "POST",
  });
}

export interface YouTubePreviewResponse {
  video_id: string;
  title: string;
  channel: string;
  duration_seconds: number;
  thumbnail_url: string;
  has_chapters: boolean;
  chapters: { title: string; start_time: number; end_time?: number }[];
}

export async function previewYouTube(url: string): Promise<YouTubePreviewResponse> {
  return apiFetch<YouTubePreviewResponse>("/api/youtube/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function uploadYouTube(
  url: string,
  options: {
    study_goal?: string;
    card_style?: CardStyle;
    deck_size?: DeckSize;
  } = {},
): Promise<UploadResponse> {
  return apiFetch<UploadResponse>("/api/youtube", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, ...options }),
  });
}

export function getExportUrl(documentId: string, format: "csv" | "apkg"): string {
  const token = getToken();
  const base = `${API_BASE}/api/documents/${documentId}/export/${format}`;
  if (token) return `${base}?token=${encodeURIComponent(token)}`;
  return base;
}
