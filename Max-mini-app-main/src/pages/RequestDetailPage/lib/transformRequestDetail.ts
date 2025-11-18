import type { RequestDetail } from "@/api/requests";
import type { RequestStatus } from "@/components/widgets/RequestCard/types";
import { formatDateTime } from "@/lib";

export interface RequestDetailViewModel {
  id: number;
  requestNumber: string;
  status: RequestStatus;
  createdAt: string;
  fullName: string;
  course: string;
  faculty: string;
  group: string;
  content: string;
}

interface StructuredContent {
  full_name?: string;
  course?: string;
  faculty?: string;
  group?: string;
  content?: string;
  description?: string;
}

const STATUS_MAP: Record<string, RequestStatus> = {
  pending: "pending",
  approved: "approved",
  rejected: "rejected",
  ready: "ready",
};

function mapStatus(status: string | null | undefined): RequestStatus {
  if (!status) {
    return "pending";
  }
  const normalized = status.toLowerCase();
  return STATUS_MAP[normalized] ?? "pending";
}

function parseContent(value: string | null | undefined): StructuredContent {
  if (!value) {
    return {};
  }
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object") {
      return parsed as StructuredContent;
    }
  } catch (error) {
    // Ignore malformed json payloads and fallback to plain text.
  }
  return {};
}

export function transformRequestDetailForPage(request: RequestDetail): RequestDetailViewModel {
  const structured = parseContent(request.content);

  return {
    id: request.id,
    requestNumber: `№${String(request.id).padStart(4, "0")}`,
    status: mapStatus(request.status),
    createdAt: formatDateTime(request.created_at),
    fullName: structured.full_name || request.author_full_name || "�?�� �?��������?�?",
    course: structured.course || "",
    faculty: structured.faculty || "",
    group: structured.group || "",
    content: structured.content || structured.description || request.content,
  };
}
