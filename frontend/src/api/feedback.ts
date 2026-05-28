import { getJson, postJson } from "./client";
import type { FeedbackPayload, FeedbackRecord, FeedbackStats } from "../types/feedback";

export function submitFeedback(token: string, payload: FeedbackPayload): Promise<FeedbackRecord> {
  return postJson<FeedbackRecord>("/api/feedback", {
    token,
    body: payload,
  });
}

export function getFeedback(token: string): Promise<FeedbackRecord[]> {
  return getJson<FeedbackRecord[]>("/api/admin/feedback", { token });
}

export function getFeedbackStats(token: string): Promise<FeedbackStats> {
  return getJson<FeedbackStats>("/api/admin/feedback/stats", { token });
}

