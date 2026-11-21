import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";

export type MeetingSummary = {
  id: number;
  title: string;
  meeting_date: string;
  created_at: string;
};

export type ActionItem = {
  id: number;
  text: string;
  owner: string | null;
  due_date: string | null;
  status: string;
};

export type MeetingDetail = MeetingSummary & {
  transcript: string;
  summary: string | null;
  decisions: string[] | null;
  analysis_status: "pending" | "done" | "failed";
  analysis_error: string | null;
  action_items: ActionItem[];
};

export type NewMeeting = { title: string; meeting_date: string; transcript: string };

export function useMeetings() {
  return useQuery({
    queryKey: ["meetings"],
    queryFn: () => api<MeetingSummary[]>("/meetings"),
  });
}

export function useMeeting(id: number) {
  return useQuery({
    queryKey: ["meetings", id],
    queryFn: () => api<MeetingDetail>(`/meetings/${id}`),
  });
}

export function useCreateMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (meeting: NewMeeting) =>
      api<MeetingDetail>("/meetings", { method: "POST", body: JSON.stringify(meeting) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useUploadMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { title: string; meeting_date: string; file: File }) => {
      const form = new FormData();
      form.append("title", input.title);
      form.append("meeting_date", input.meeting_date);
      form.append("file", input.file);
      return api<MeetingDetail>("/meetings/upload", { method: "POST", body: form });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useAnalyseMeeting(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api<MeetingDetail>(`/meetings/${id}/analyse`, { method: "POST" }),
    onSuccess: (meeting) => {
      queryClient.setQueryData(["meetings", id], meeting);
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
    onError: () => {
      // A failed run is saved on the server, so reload the meeting to show its failed state.
      queryClient.invalidateQueries({ queryKey: ["meetings", id] });
    },
  });
}

export function useDeleteMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api<void>(`/meetings/${id}?confirm=true`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}
