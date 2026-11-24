import { useState } from "react";
import { Link } from "react-router-dom";
import { useShareToSlack } from "../editing";
import { useSlackConnection } from "../slack";

export function ShareToSlack({ meetingId }: { meetingId: number }) {
  const connection = useSlackConnection();
  const share = useShareToSlack(meetingId);
  const [sent, setSent] = useState(false);
  const connected = connection.data?.connected;

  return (
    <section className="card">
      <h2>Share</h2>
      {connection.isPending ? (
        <p className="muted">Checking your Slack channel...</p>
      ) : !connected ? (
        <p>
          Connect your Slack channel on the <Link to="/account">Account page</Link> first.
        </p>
      ) : (
        <>
          <p className="muted">Post this meeting's summary, decisions and action items to your Slack channel.</p>
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
            {share.isPending ? "Sending..." : sent ? "Send again" : "Send to Slack"}
          </button>
        </>
      )}
    </section>
  );
}
