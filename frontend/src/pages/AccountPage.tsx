import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";
import { useRemoveSlackConnection, useSaveSlackConnection, useSlackConnection } from "../slack";

export default function AccountPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: user } = useMe();

  const deleteAccount = useMutation({
    mutationFn: () => api<void>("/auth/me", { method: "DELETE" }),
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(["me"], null);
      navigate("/login", { replace: true });
    },
  });

  const slack = useSlackConnection();
  const saveSlack = useSaveSlackConnection();
  const removeSlack = useRemoveSlackConnection();
  const [webhook, setWebhook] = useState("");

  function saveWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saveSlack.isPending || !webhook.trim()) return;
    saveSlack.mutate(webhook.trim(), { onSuccess: () => setWebhook("") });
  }

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

      <div className="card">
        <h2>Slack</h2>
        <p className="muted">
          Paste an incoming webhook URL from your Slack workspace. Meetings you share will post to that
          channel. The URL is stored encrypted and is never shown again.
        </p>
        <p>
          <span className="badge">{slack.data?.connected ? "Connected" : "Not connected"}</span>
        </p>
        <form className="item-form" onSubmit={saveWebhook}>
          <label>
            Webhook URL
            <input
              type="url"
              value={webhook}
              onChange={(e) => setWebhook(e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
            />
          </label>
          {saveSlack.isError && (
            <p role="alert" className="error">
              {saveSlack.error instanceof Error ? saveSlack.error.message : "Could not save the Slack channel"}
            </p>
          )}
          {removeSlack.isError && (
            <p role="alert" className="error">
              {removeSlack.error instanceof Error ? removeSlack.error.message : "Could not disconnect Slack"}
            </p>
          )}
          <div className="button-row">
            <button type="submit" disabled={saveSlack.isPending || !webhook.trim()}>
              {saveSlack.isPending ? "Saving..." : "Save Slack channel"}
            </button>
            {slack.data?.connected && (
              <button type="button" onClick={() => removeSlack.mutate()} disabled={removeSlack.isPending}>
                Disconnect
              </button>
            )}
          </div>
        </form>
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
          {deleteAccount.isPending ? "Deleting..." : "Delete my account"}
        </button>
      </div>
    </main>
  );
}
