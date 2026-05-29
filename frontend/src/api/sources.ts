import { deleteJson, getJson, patchJson, postJson } from "./client";
import type { IndexSourceResponse, SourceCreatePayload, SourceRecord, SourceUpdatePayload } from "../types/source";

export function getSources(token: string): Promise<SourceRecord[]> {
  return getJson<SourceRecord[]>("/api/sources", { token });
}

export function createSource(token: string, payload: SourceCreatePayload): Promise<SourceRecord> {
  return postJson<SourceRecord>("/api/sources", {
    token,
    body: payload,
  });
}

export function updateSource(token: string, sourceId: number, payload: SourceUpdatePayload): Promise<SourceRecord> {
  return patchJson<SourceRecord>(`/api/sources/${sourceId}`, {
    token,
    body: payload,
  });
}

export function deleteSource(token: string, sourceId: number): Promise<void> {
  return deleteJson<void>(`/api/sources/${sourceId}`, { token });
}

export function indexSource(token: string, sourceId: number): Promise<IndexSourceResponse> {
  return postJson<IndexSourceResponse>(`/api/sources/${sourceId}/index`, { token });
}
