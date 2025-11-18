import type { LibraryAccess } from "@/api/library";

export interface LibraryAccessViewModel {
  id: string;
  login: string;
  password: string;
  portalUrl: string;
  libraries: string[];
  instructions: string;
}

const URL_REGEXP = /(https?:\/\/[^\s]+)/gi;

function extractUrls(value: string | null | undefined): string[] {
  if (!value) {
    return [];
  }

  const matches = value.match(URL_REGEXP) ?? [];
  return matches.map((url) => url.trim());
}

export function transformLibraryAccessForPage(access: LibraryAccess): LibraryAccessViewModel {
  const instructionUrls = extractUrls(access.instructions);
  const candidateUrls = [access.portal_url, ...instructionUrls].filter(Boolean) as string[];
  const uniqueUrls = Array.from(new Set(candidateUrls));

  return {
    id: access.id,
    login: access.login,
    password: access.password,
    portalUrl: access.portal_url,
    libraries: uniqueUrls,
    instructions: access.instructions || "",
  };
}
