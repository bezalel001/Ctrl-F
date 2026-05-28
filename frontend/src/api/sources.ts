import { getJson, postJson } from "./client";
import type { IndexSourceResponse, SourceCreatePayload, SourceRecord } from "../types/source";

export function getSources(token: string): Promise<SourceRecord[]> {
  return getJson<SourceRecord[]>("/api/sources", { token });
}

export function createSource(token: string, payload: SourceCreatePayload): Promise<SourceRecord> {
  return postJson<SourceRecord>("/api/sources", {
    token,
    body: payload,
  });
}

export function indexSource(token: string, sourceId: number): Promise<IndexSourceResponse> {
  return postJson<IndexSourceResponse>(`/api/sources/${sourceId}/index`, { token });
}

