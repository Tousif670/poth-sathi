/**
 * Auth Helper Module (Firebase Auth REST / Emulator / Token persistence).
 * Per AGENTS.md Rule 3: Never import or use the Firestore client SDK in frontend code.
 */

export interface AuthTokenSession {
  uid: string;
  idToken: string;
  authProvider: "anonymous" | "google" | "email";
}

const STORAGE_KEY = "pothsathi_auth_session";

export function getStoredAuthSession(): AuthTokenSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthTokenSession;
    if (parsed && typeof parsed.uid === "string" && typeof parsed.idToken === "string") {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

export function setStoredAuthSession(session: AuthTokenSession | null): void {
  if (typeof window === "undefined") return;
  try {
    if (!session) {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
  } catch {
    // Ignore storage quota errors
  }
}

export async function signInAnonymouslyViaAuth(): Promise<AuthTokenSession> {
  const emulatorHost =
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST?.trim() || "localhost:9099";
  const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY?.trim() || "fake-api-key";
  const useEmulator =
    !process.env.NEXT_PUBLIC_FIREBASE_API_KEY ||
    Boolean(process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST);

  const endpoint = useEmulator
    ? `http://${emulatorHost}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=${apiKey}`
    : `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${apiKey}`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ returnSecureToken: true }),
  });

  if (!response.ok) {
    throw new Error(`Anonymous sign-in failed (${response.status})`);
  }

  const data = (await response.json()) as { localId?: string; idToken?: string };
  if (!data.localId || !data.idToken) {
    throw new Error("Invalid Auth response: missing localId or idToken");
  }

  const session: AuthTokenSession = {
    uid: data.localId,
    idToken: data.idToken,
    authProvider: "anonymous",
  };
  setStoredAuthSession(session);
  return session;
}
