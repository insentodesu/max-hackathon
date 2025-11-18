import { useMemo } from "react";
import type { UserRole } from "@/components/shared/BottomNavigation/BottomNavigation";
import { useUserRoleData } from "./useUserRoleData";

/**
 * Normalises MAX role payload into one of UI specific roles.
 */
export function useUserRole(defaultRole: UserRole = "teacher"): UserRole {
  const { data } = useUserRoleData();

  return useMemo(() => {
    if (!data?.role) {
      return defaultRole;
    }

    const role = data.role.toLowerCase();
    if (role.includes("admin")) {
      return "admin";
    }
    if (role.includes("teacher") || role.includes("staff")) {
      return "teacher";
    }
    return "student";
  }, [data?.role, defaultRole]);
}
