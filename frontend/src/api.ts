export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isForm = options.body instanceof FormData;
  const response = await fetch(`/api${path}`, {
    ...options,
    // Sends the session cookie with every request.
    credentials: "include",
    // File uploads set their own content type, so only JSON bodies get this header.
    headers: isForm
      ? options.headers
      : { "Content-Type": "application/json", ...(options.headers as Record<string, string>) },
  });

  if (response.status === 204) return undefined as T;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, readError(data));
  }
  return data as T;
}

function readError(data: unknown): string {
  // FastAPI sends { detail: "text" } for our own errors,
  // and { detail: [{ msg, ... }] } for validation errors.
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  return "Something went wrong. Please try again.";
}