const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

function stripTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

/**
 * Builds url that can be used for downloading documents from API/static storage.
 */
export function getDocumentUrl(path: string): string {
  if (!path) {
    return "";
  }

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  if (path.startsWith("/static/")) {
    const baseWithoutApi = API_BASE_URL.replace(/\/api\/v1$/, "");
    return `${stripTrailingSlash(baseWithoutApi)}${path}`;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${stripTrailingSlash(API_BASE_URL)}${normalizedPath}`;
}
