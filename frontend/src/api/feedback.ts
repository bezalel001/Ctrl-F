import { getJson, postJson } from "./client";
import type { FeedbackFilters, FeedbackPayload, FeedbackRecord, FeedbackStats } from "../types/feedback";

export function submitFeedback(token: string, payload: FeedbackPayload): Promise<FeedbackRecord> {
  return postJson<FeedbackRecord>("/api/feedback", {
    token,
    body: payload,
  });
}

export function getFeedback(token: string, filters: FeedbackFilters = {}): Promise<FeedbackRecord[]> {
  return getJson<FeedbackRecord[]>(`/api/admin/feedback${filterQuery(filters)}`, { token });
}

export function getFeedbackStats(token: string, filters: FeedbackFilters = {}): Promise<FeedbackStats> {
  return getJson<FeedbackStats>(`/api/admin/feedback/stats${filterQuery(filters)}`, { token });
}

function filterQuery(filters: FeedbackFilters): string {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  });

  const query = params.toString();
  return query ? `?${query}` : "";
}
