import type { UserProfile } from "@/api/users";

type ApiProfileWithAvatar = UserProfile & { avatar_url?: string | null };

export interface ProfileViewModel {
  fullName: string;
  role: string;
  course: string;
  faculty: string;
  group: string;
  placeOfStudy: string;
  studentId: string;
  placeOfWork: string;
  position: string;
  tabNumber: string;
  avatarUrl: string | null;
}

function splitCourseFacultyGroup(value: string | null): [string, string, string] {
  if (!value) {
    return ["", "", ""];
  }

  const parts = value.split(",").map((item) => item.trim());
  return [parts[0] ?? "", parts[1] ?? "", parts[2] ?? ""];
}

export function transformProfileForPage(profile: UserProfile): ProfileViewModel {
  const [course, faculty, group] = splitCourseFacultyGroup(profile.course_faculty_group);
  const profileWithAvatar = profile as ApiProfileWithAvatar;

  return {
    fullName: profile.full_name,
    role: profile.role || "",
    course,
    faculty,
    group,
    placeOfStudy: profile.place_of_study || "�?�� �?��������?�?",
    studentId: profile.student_card || "�?�� �?��������?�?",
    placeOfWork: profile.place_of_work || profile.kafedra || "�?�� �?��������?�?",
    position: profile.kafedra || profile.role || "�?�� �?��������?�?",
    tabNumber: profile.tab_number || "�?�� �?��������?�?",
    avatarUrl: profileWithAvatar.avatar_url || null,
  };
}
