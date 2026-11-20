import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "./api";

export type User = { id: number; email: string };

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    retry: false,
    queryFn: async () => {
      try {
        return await api<User>("/auth/me");
      } catch (error) {
        // A 401 just means nobody is logged in. That's a normal state, not an error.
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
  });
}