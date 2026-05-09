import { useQuery } from "@tanstack/react-query";

import { api, type Me } from "../api";

export function useSession() {
  return useQuery<Me>({
    queryKey: ["me"],
    queryFn: () => api.get<Me>("/api/auth/me"),
    retry: false,
    staleTime: 30_000,
  });
}
