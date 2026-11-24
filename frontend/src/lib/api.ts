export interface BackendErrorPayload {
  error: {
    code: string;
    message_bn: string;
    message_en: string;
  };
}

export class ApiError extends Error {
  readonly code: string;
  readonly messageBn: string;
  readonly messageEn: string;
  readonly status: number;

  constructor(params: {
    code: string;
    messageEn: string;
    messageBn: string;
    status: number;
  }) {
    super(params.messageEn);
    this.name = "ApiError";
    this.code = params.code;
    this.messageEn = params.messageEn;
    this.messageBn = params.messageBn;
    this.status = params.status;
  }
}

export interface ApiRequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

function isBackendErrorPayload(data: unknown): data is BackendErrorPayload {
  if (typeof data !== "object" || data === null || !("error" in data)) {
    return false;
  }
  const err = (data as { error: unknown }).error;
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    typeof (err as { code: unknown }).code === "string" &&
    "message_en" in err &&
    typeof (err as { message_en: unknown }).message_en === "string" &&
    "message_bn" in err &&
    typeof (err as { message_bn: unknown }).message_bn === "string"
  );
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${getApiBaseUrl()}/api/v1${normalizedPath}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...options.headers,
  };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (options.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: options.signal,
    });
  } catch {
    throw new ApiError({
      code: "NETWORK_ERROR",
      messageEn:
        "Unable to reach the backend server. Please make sure the server is running and try again.",
      messageBn:
        "ব্যাকএন্ড সার্ভারের সাথে সংযোগ করা যায়নি। অনুগ্রহ করে সার্ভার চালু আছে কিনা দেখুন এবং আবার চেষ্টা করুন।",
      status: 0,
    });
  }

  let data: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      if (!response.ok) {
        throw new ApiError({
          code: `HTTP_${response.status}`,
          messageEn: `Request failed with status ${response.status}.`,
          messageBn: `অনুরোধ ব্যর্থ হয়েছে (স্ট্যাটাস ${response.status})।`,
          status: response.status,
        });
      }
      throw new ApiError({
        code: "INVALID_RESPONSE",
        messageEn: "Received an invalid JSON response from the server.",
        messageBn: "সার্ভার থেকে সঠিক তথ্য পাওয়া যায়নি।",
        status: response.status,
      });
    }
  }

  if (!response.ok) {
    if (isBackendErrorPayload(data)) {
      throw new ApiError({
        code: data.error.code,
        messageEn: data.error.message_en,
        messageBn: data.error.message_bn,
        status: response.status,
      });
    }
    throw new ApiError({
      code: `HTTP_${response.status}`,
      messageEn: `Request failed with status ${response.status}.`,
      messageBn: `অনুরোধ ব্যর্থ হয়েছে (স্ট্যাটাস ${response.status})।`,
      status: response.status,
    });
  }

  return data as T;
}
