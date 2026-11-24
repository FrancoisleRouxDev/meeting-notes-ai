import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { api } from "./api";

export type MeetingEdits = {
  title?: string;
  summary?: string;
  decisions?: string[];
};

export type ActionItemEdits = {
  text?: string;
  owner?: string | null;
  due_date?: string | null;
  status?: string;
};

export type NewActionItem = {
  text: string;
  owner: string | null;
  due_date: string | null;
  status: string;
};

// Reloads the meeting and the open items list after any change.
function refreshAll(queryClient: QueryClient, meetingId: number) {
  queryClient.invalidateQueries({ queryKey: ["meetings", meetingId] });
  queryClient.invalidateQueries({ queryKey: ["action-items"] });
}

export function useUpdateMeeting(meetingId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (edits: MeetingEdits) =>
      api(`/meetings/${meetingId}`, { method: "PATCH", body: JSON.stringify(edits) }),
    onSuccess: () => refreshAll(queryClient, meetingId),
  });
}

export function useAddActionItem(meetingId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (item: NewActionItem) =>
      api(`/meetings/${meetingId}/action-items`, { method: "POST", body: JSON.stringify(item) }),
    onSuccess: () => refreshAll(queryClient, meetingId),
  });
}

export function useUpdateActionItem(meetingId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, edits }: { itemId: number; edits: ActionItemEdits }) =>
      api(`/action-items/${itemId}`, { method: "PATCH", body: JSON.stringify(edits) }),
    onSuccess: () => refreshAll(queryClient, meetingId),
  });
}

export function useDeleteActionItem(meetingId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: number) => api<void>(`/action-items/${itemId}`, { method: "DELETE" }),
    onSuccess: () => refreshAll(queryClient, meetingId),
  });
}

export function useShareToSlack(meetingId: number) {
  return useMutation({
    mutationFn: () => api<{ sent: boolean }>(`/integrations/slack/share/${meetingId}`, { method: "POST" }),
  });
}

