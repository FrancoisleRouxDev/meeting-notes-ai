import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";

export default function AccountPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: user } = useMe();

  const deleteAccount = useMutation({
    mutationFn: () => api<void>("/auth/me", { method: "DELETE" }),
    onSuccess: () => {
      // The account is gone, so drop everything cached for it and go to the login page.
      queryClient.clear();
      queryClient.setQueryData(["me"], null);
      navigate("/login", { replace: true });
    },
  });

  function handleDelete() {
    const sure = window.confirm(
      "Delete your account? You will be logged out and won't be able to log in again. Your meetings will no longer be accessible.",
    );
    if (sure) deleteAccount.mutate();
  }

  return (
    <main>
      <h1>Account</h1>

      <div className="card">
        <p className="muted">Signed in as</p>
        <p className="account-email">{user?.email}</p>
      </div>

      <div className="card danger-zone">
        <h2>Delete account</h2>
        <p>
          Deleting your account logs you out and blocks future logins. Your meetings and action items
          are no longer accessible to you.
        </p>
        {deleteAccount.isError && (
          <p role="alert" className="error">
            {deleteAccount.error instanceof Error ? deleteAccount.error.message : "Could not delete the account"}
          </p>
        )}
        <button className="danger" onClick={handleDelete} disabled={deleteAccount.isPending}>
          {deleteAccount.isPending ? "Deleting…" : "Delete my account"}
        </button>
      </div>
    </main>
  );
}
