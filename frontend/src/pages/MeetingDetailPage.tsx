import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api";
import { useAnalyseMeeting, useDeleteMeeting, useMeeting } from "../meetings";

const statusLabels = {
  pending: "Not analysed yet",
  done: "Analysis complete",
  failed: "Analysis failed",
} as const;

export default function MeetingDetailPage() {
  const { id } = useParams();
  const meetingId = Number(id);
  const navigate = useNavigate();

  const { data: meeting, isPending, isError, error } = useMeeting(meetingId);
  const analyse = useAnalyseMeeting(meetingId);
  const remove = useDeleteMeeting();

  if (isPending) {
    return (
      <main>
        <p role="status">Loading meeting…</p>
      </main>
    );
  }

  if (isError) {
    const notFound = error instanceof ApiError && error.status === 404;
    return (
      <main>
        <p role="alert" className="error">
          {notFound ? "This meeting doesn't exist." : error.message}
        </p>
        <Link to="/meetings">Back to meetings</Link>
      </main>
    );
  }

  const title = meeting.title;  

  function handleDelete() {
    // Deleting is permanent, so ask first. Only a confirmed delete sends confirm=true.
    const sure = window.confirm(
      `Delete "${title}"? Its transcript, summary and action items will be removed permanently. This can't be undone.`,
    );
    if (!sure) return;
    remove.mutate(meetingId, { onSuccess: () => navigate("/meetings", { replace: true }) });
  }

  const label =
    meeting.analysis_status === "failed"
      ? "Try analysis again"
      : "Analyse transcript";

  return (
    <main>
      <p>
        <Link to="/meetings">← All meetings</Link>
      </p>
      <h1>{meeting.title}</h1>
      <p className="muted">
        {meeting.meeting_date} · <span className="badge">{statusLabels[meeting.analysis_status]}</span>
      </p>

      {meeting.analysis_status === "failed" && (
        <p role="alert" className="error">
          The last analysis failed ({meeting.analysis_error}). Your transcript is safe, so you can try again.
        </p>
      )}
      {analyse.isError && <p role="alert" className="error">{analyse.error.message}</p>}
      {remove.isError && <p role="alert" className="error">{remove.error.message}</p>}

      {meeting.analysis_status !== "done" && (
        <button onClick={() => analyse.mutate()} disabled={analyse.isPending}>
          {analyse.isPending ? "Analysing… this can take a minute" : label}
        </button>
      )}

      {meeting.analysis_status === "done" && (
        <>
          <section>
            <h2>Summary</h2>
            <p>{meeting.summary}</p>
          </section>
          <section>
            <h2>Decisions</h2>
            {meeting.decisions && meeting.decisions.length > 0 ? (
              <ul>
                {meeting.decisions.map((decision, index) => (
                  <li key={index}>{decision}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">No decisions were recorded.</p>
            )}
          </section>
        </>
      )}

      <section>
        <h2>Action items</h2>
        {meeting.action_items.length === 0 ? (
          <p className="muted">
            {meeting.analysis_status === "done"
              ? "No action items were found."
              : "Run analysis to find action items."}
          </p>
        ) : (
          <ul className="action-items">
            {meeting.action_items.map((item) => (
              <li key={item.id}>
                <span>{item.text}</span>
                <span className="muted">
                  {" "}· Owner: {item.owner ?? "not stated"} · Due: {item.due_date ?? "not stated"} · {item.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <details>
        <summary>Transcript</summary>
        <pre className="transcript">{meeting.transcript}</pre>
      </details>

      <section>
        <button className="danger" onClick={handleDelete} disabled={remove.isPending}>
          {remove.isPending ? "Deleting…" : "Delete meeting"}
        </button>
      </section>
    </main>
  );
}