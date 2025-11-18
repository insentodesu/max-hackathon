import type { Elective } from "@/api/electives";
import type { ElectiveCardStatus } from "@/components/widgets/ElectiveCard/types";

export interface ElectiveCardViewModel {
  id: string;
  title: string;
  year: string;
  period: string;
  status: ElectiveCardStatus;
  progress: number;
}

function calculateProgress(current: number, max: number): number {
  if (max <= 0) {
    return 0;
  }
  const percent = (current / max) * 100;
  return Math.max(0, Math.min(100, Math.round(percent)));
}

function getStatus(elective: Elective): ElectiveCardStatus {
  if (!elective.is_active) {
    return "finished";
  }
  return "available";
}

export function transformElectiveForCard(elective: Elective): ElectiveCardViewModel {
  return {
    id: elective.id,
    title: elective.title,
    year: new Date(elective.created_at).getFullYear().toString(),
    period: elective.schedule_info || elective.teacher_full_name || "�?�� �?��������?�?",
    status: getStatus(elective),
    progress: calculateProgress(elective.current_students, elective.max_students),
  };
}
