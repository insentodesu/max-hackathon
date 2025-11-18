import { useMemo } from "react";
import { useUserRoleQuery } from "@/hooks/queries";
import { getMaxId } from "@/constants/maxId";

/**
 * Lightweight wrapper that hides the logic of reading max id and feeding it into the query.
 */
export function useUserRoleData() {
  const maxId = useMemo(() => getMaxId(), []);
  return useUserRoleQuery(maxId);
}
