import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";

// Temporary page. The meeting list replaces this in the next step.
export default function MeetingsPage() {
  const { data: user } = useMe();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const logout = useMutation({
    mutationFn: () => api<void>("/auth/logout", { method: "POST" }),
    onSettled: () => {
      queryClient.setQueryData(["me"], null);
      navigate("/login", { replace: true });
    },
  });

  return (
    <main>
      <h1>Meetings</h1>
      <p>Signed in as {user?.email}</p>
      <button onClick={() => logout.mutate()} disabled={logout.isPending}>
        Log out
      </button>
    </main>
  );
}