import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export type OpenItem = {
  id: number;
  text: string;
  owner: string | null;
  due_date: string | null;
  status: string;
  meeting_id: number;
  meeting_title: string;
};

export type ItemFilters = {
  status: string;
  owner: string;
  overdue: boolean;
};

export function useOpenItems(filters: ItemFilters) {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.owner.trim()) params.set("owner", filters.owner.trim());
  if (filters.overdue) params.set("overdue", "true");
  const query = params.toString();

  return useQuery({
    queryKey: ["action-items", filters],
    queryFn: () => api<OpenItem[]>(`/action-items${query ? `?${query}` : ""}`),
  });
}
