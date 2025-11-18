const TOKEN_STORAGE_KEY = "access_token";
const MAX_ID_STORAGE_KEY = "max_id";

/**
 * Persists auth token in localStorage for reuse inside axios interceptors.
 */
export function saveToken(token: string) {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch (error) {
    console.error("Failed to save token to localStorage:", error);
  }
  return token;
}

/**
 * Returns auth token from localStorage if it was stored earlier.
 */
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error("Failed to read token from localStorage:", error);
    return null;
  }
}

/**
 * Saves MAX Bridge user identifier in localStorage to simplify token refresh flow.
 */
export function saveMaxId(maxId: number) {
  try {
    localStorage.setItem(MAX_ID_STORAGE_KEY, String(maxId));
  } catch (error) {
    console.error("Failed to save max_id to localStorage:", error);
  }
}

/**
 * Reads MAX Bridge identifier from storage if it exists.
 */
export function getMaxIdFromStorage(): number | null {
  try {
    const value = localStorage.getItem(MAX_ID_STORAGE_KEY);
    if (!value) {
      return null;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  } catch (error) {
    console.error("Failed to read max_id from localStorage:", error);
    return null;
  }
}

/**
 * Clears auth token if user logs out or token becomes invalid.
 */
export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear token from localStorage:", error);
  }
}
