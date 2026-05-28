const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface RequestOptions {
  token?: string;
  body?: unknown;
}

export async function getJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return requestJson<T>("GET", path, options);
}

export async function postJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return requestJson<T>("POST", path, options);
}

export async function patchJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return requestJson<T>("PATCH", path, options);
}

async function requestJson<T>(method: string, path: string, options: RequestOptions): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = typeof payload?.detail === "string" ? payload.detail : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}
