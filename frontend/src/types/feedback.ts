import type { ChatSource } from "./chat";

export type FeedbackRating = "helpful" | "not_helpful";

export interface FeedbackPayload {
  message_id: string;
  rating: FeedbackRating;
  question: string;
  answer: string;
  confidence: number;
  sources: ChatSource[];
  comment: string | null;
}

export interface FeedbackRecord extends FeedbackPayload {
  id: number;
  user_id: string;
  created_at: string;
}

export interface FeedbackStats {
  total: number;
  helpful: number;
  not_helpful: number;
}

