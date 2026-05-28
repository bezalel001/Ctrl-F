import { postJson } from "./client";
import type { ChatResponse } from "../types/chat";

export function sendChatMessage(
  token: string,
  question: string,
  conversationId: string | null,
): Promise<ChatResponse> {
  return postJson<ChatResponse>("/api/chat", {
    token,
    body: {
      question,
      conversation_id: conversationId,
    },
  });
}

