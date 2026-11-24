import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";

export function useSlackConnection() {
  return useQuery({
    queryKey: ["slack-connection"],
    queryFn: () => api<{ connected: boolean }>("/integrations/slack/connection"),
  });
}

export function useSaveSlackConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (url: string) =>
      api<{ connected: boolean }>("/integrations/slack/connection", {
        method: "PUT",
        body: JSON.stringify({ url }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["slack-connection"] }),
  });
}

export function useRemoveSlackConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api<void>("/integrations/slack/connection", { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["slack-connection"] }),
  });
}
