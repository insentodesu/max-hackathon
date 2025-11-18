import type { ApprovalRequest } from "@/api/requests";
import type { RequestStatus } from "@/components/widgets/RequestCard/types";
import { formatDateTime } from "@/lib";

export interface RequestCardViewModel {
  id: string;
  requestNumber: string;
  date: string;
  status: RequestStatus;
  description: string;
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
  const normalised = status.toLowerCase();
  return STATUS_MAP[normalised] ?? "pending";
}

export function transformRequestForCard(request: ApprovalRequest): RequestCardViewModel {
  return {
    id: String(request.id),
    requestNumber: `№${String(request.id).padStart(4, "0")}`,
    date: formatDateTime(request.created_at),
    status: mapStatus(request.status),
    description: request.content || "�?�� �?��������?�?",
  };
}
