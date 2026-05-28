export interface ChatSource {
  source_id: number;
  title: string;
  location: string;
  excerpt: string;
  score: number;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: ChatSource[];
  confidence: number;
  warning: string | null;
  suggested_contacts: string[];
}

