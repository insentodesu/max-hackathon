import fallbackImage from "@/assets/images/event-heart.jpg";
import { useUserRoleData } from "./useUserRoleData";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const HTTP_SCHEME_REGEX = /^https?:\/\//i;

function stripTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function buildAbsoluteAssetUrl(path: string | null | undefined): string {
  if (!path) {
    return fallbackImage;
  }

  if (HTTP_SCHEME_REGEX.test(path) || path.startsWith("data:")) {
    return path;
  }

  const base = API_BASE_URL || "";

  if (path.startsWith("/static/")) {
    const baseWithoutApi = base.replace(/\/api\/v1$/, "");
    return `${stripTrailingSlash(baseWithoutApi)}${path}`;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${stripTrailingSlash(base)}${normalizedPath}`;
}

/**
 * Formats API date/time strings into a human readable RU locale format.
 */
export function formatDateTime(value: string | number | Date | null | undefined): string {
  if (!value) {
    return "";
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function preloadImage(url: string): Promise<string> {
  if (typeof Image === "undefined") {
    return Promise.resolve(url);
  }

  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(url);
    img.onerror = () => resolve(fallbackImage);
    img.src = url;
  });
}

/**
 * Returns a valid URL for image resources from API.
 * Falls back to bundled placeholder if original image is missing/unreachable.
 */
export async function getImageUrl(path: string | null | undefined): Promise<string> {
  const url = buildAbsoluteAssetUrl(path);
  return preloadImage(url);
}

/**
 * Returns processed URL without preloading (useful in synchronous flows).
 */
export function getImageUrlSync(path: string | null | undefined): string {
  return buildAbsoluteAssetUrl(path);
}

export { useUserRoleData };
