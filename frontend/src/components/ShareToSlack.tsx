import { useState } from "react";
import { useShareToSlack } from "../editing";

export function ShareToSlack({ meetingId }: { meetingId: number }) {
  const share = useShareToSlack(meetingId);
  const [sent, setSent] = useState(false);

  return (
    <section className="card">
      <h2>Share</h2>
      <p className="muted">Post this meeting's summary, decisions and action items to the team's Slack channel.</p>
      {share.isError && (
        <p role="alert" className="error">
          {share.error instanceof Error ? share.error.message : "Could not send to Slack"}
        </p>
      )}
      {sent && !share.isError && <p role="status">Sent to Slack.</p>}
      <button
        type="button"
        disabled={share.isPending}
        onClick={() => share.mutate(undefined, { onSuccess: () => setSent(true) })}
      >
        {share.isPending ? "Sending…" : sent ? "Send again" : "Send to Slack"}
      </button>
    </section>
  );
}
