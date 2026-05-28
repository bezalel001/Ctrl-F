import { getJson, postJson } from "./client";
import type { AuthResponse, UserProfile } from "../types/auth";

export function login(email: string, password: string): Promise<AuthResponse> {
  return postJson<AuthResponse>("/api/auth/login", {
    body: { email, password },
  });
}

export function getCurrentUser(token: string): Promise<UserProfile> {
  return getJson<UserProfile>("/api/auth/me", { token });
}

