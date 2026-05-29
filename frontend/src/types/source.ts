export interface SourceRecord {
  id: number;
  title: string;
  description: string | null;
  source_type: string;
  location: string;
  owning_department: string;
  allowed_roles: string[];
  allowed_departments: string[];
  approval_status: string;
  version: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  indexed_at: string | null;
}

export interface SourceCreatePayload {
  title: string;
  description: string | null;
  source_type: string;
  location: string;
  owning_department: string;
  allowed_roles: string[];
  allowed_departments: string[];
  approval_status: string;
  version: string;
}

export type SourceUpdatePayload = Partial<SourceCreatePayload>;

export interface IndexSourceResponse {
  source_id: number;
  chunk_count: number;
  collection: string;
  indexed_at: string;
}
