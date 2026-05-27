import { getJson } from "./client";
import type { HealthResponse } from "../types/health";

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

