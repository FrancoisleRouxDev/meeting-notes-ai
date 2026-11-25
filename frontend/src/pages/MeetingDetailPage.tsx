import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api";
import { ShareToSlack } from "../components/ShareToSlack";
import { useAddActionItem, useDeleteActionItem, useUpdateActionItem, useUpdateMeeting } from "../editing";
import {
  useAnalyseMeeting,
  useDeleteMeeting,
  useMeeting,
  type ActionItem,
  type MeetingDetail,
} from "../meetings";

const statusLabels = {
  pending: "Not analysed yet",
  done: "Analysis complete",
  failed: "Analysis failed",
} as const;

const STATUSES = ["to do", "in progress", "done"];

function errorText(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export default function MeetingDetailPage() {
  const { id } = useParams();
  const meetingId = Number(id);
  const navigate = useNavigate();
  const location = useLocation();
  const [sourceJumpRequest, setSourceJumpRequest] = useState(0);
  const transcriptDetails = useRef<HTMLDetailsElement>(null);
  const sourceLineMatch = /^#transcript-line-(\d+)$/.exec(location.hash);
  const sourceLineToShow = sourceLineMatch ? Number(sourceLineMatch[1]) : null;

  const { data: meeting, isPending, isError, error } = useMeeting(meetingId);
  const analyse = useAnalyseMeeting(meetingId);
  const remove = useDeleteMeeting();

  useEffect(() => {
    if (meeting && sourceLineToShow !== null && transcriptDetails.current) {
      transcriptDetails.current.open = true;
      document
        .getElementById(`transcript-line-${sourceLineToShow}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [meeting, sourceJumpRequest, sourceLineToShow]);

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

  const label = meeting.analysis_status === "failed" ? "Try analysis again" : "Analyse transcript";

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

      <ShareToSlack meetingId={meetingId} />



      <MeetingNotes meeting={meeting} />

      <ActionItems
        meetingId={meetingId}
        items={meeting.action_items}
        analysisDone={meeting.analysis_status === "done"}
        onSourceClick={() => setSourceJumpRequest((request) => request + 1)}
      />

      <details ref={transcriptDetails}>
        <summary>Transcript</summary>
        <pre className="transcript">
          {meeting.transcript.split(/\r\n|\r|\n/).map((line, index) => {
            const lineNumber = index + 1;
            return (
              <span
                id={`transcript-line-${lineNumber}`}
                className={`transcript-line${sourceLineToShow === lineNumber ? " highlighted" : ""}`}
                key={lineNumber}
              >
                <span className="transcript-line-number" aria-hidden="true">{lineNumber}</span>
                {line || " "}
              </span>
            );
          })}
        </pre>
      </details>

      <section>
        <button className="danger" onClick={handleDelete} disabled={remove.isPending}>
          {remove.isPending ? "Deleting…" : "Delete meeting"}
        </button>
      </section>
    </main>
  );
}

function MeetingNotes({ meeting }: { meeting: MeetingDetail }) {
  const update = useUpdateMeeting(meeting.id);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [decisions, setDecisions] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function startEditing() {
    setTitle(meeting.title);
    setSummary(meeting.summary ?? "");
    setDecisions((meeting.decisions ?? []).join("\n"));
    setFormError(null);
    setEditing(true);
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (update.isPending) return;
    if (!title.trim()) {
      setFormError("Give the meeting a title.");
      return;
    }
    setFormError(null);
    update.mutate(
      {
        title: title.trim(),
        summary: summary.trim(),
        decisions: decisions
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean),
      },
      { onSuccess: () => setEditing(false) },
    );
  }

  if (editing) {
    return (
      <section>
        <h2>Edit details</h2>
        <form className="form" onSubmit={save}>
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
          </label>
          <label>
            Summary
            <textarea rows={5} value={summary} onChange={(e) => setSummary(e.target.value)} maxLength={5000} />
          </label>
          <label>
            Decisions (one per line)
            <textarea rows={5} value={decisions} onChange={(e) => setDecisions(e.target.value)} />
          </label>
          {formError && <p role="alert" className="error">{formError}</p>}
          {update.isError && <p role="alert" className="error">{errorText(update.error, "Could not save")}</p>}
          <div className="button-row">
            <button type="submit" disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setEditing(false)} disabled={update.isPending}>
              Cancel
            </button>
          </div>
        </form>
      </section>
    );
  }

  return (
    <>
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
      <p>
        <button type="button" onClick={startEditing}>
          Edit details
        </button>
      </p>
    </>
  );
}

function ActionItems({
  meetingId,
  items,
  analysisDone,
  onSourceClick,
}: {
  meetingId: number;
  items: ActionItem[];
  analysisDone: boolean;
  onSourceClick: () => void;
}) {
  return (
    <section>
      <h2>Action items</h2>
      {items.length === 0 ? (
        <p className="muted">
          {analysisDone ? "No action items yet." : "Run analysis to find action items, or add one below."}
        </p>
      ) : (
        <ul className="action-items">
          {items.map((item) => (
            <ActionItemRow
              key={item.id}
              meetingId={meetingId}
              item={item}
              onSourceClick={onSourceClick}
            />
          ))}
        </ul>
      )}
      <AddActionItem meetingId={meetingId} />
    </section>
  );
}

function ActionItemRow({
  meetingId,
  item,
  onSourceClick,
}: {
  meetingId: number;
  item: ActionItem;
  onSourceClick: () => void;
}) {
  const update = useUpdateActionItem(meetingId);
  const remove = useDeleteActionItem(meetingId);
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [owner, setOwner] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [status, setStatus] = useState("to do");
  const [formError, setFormError] = useState<string | null>(null);
  const busy = update.isPending || remove.isPending;

  function startEditing() {
    setText(item.text);
    setOwner(item.owner ?? "");
    setDueDate(item.due_date ?? "");
    setStatus(item.status);
    setFormError(null);
    setEditing(true);
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (update.isPending) return;
    if (!text.trim()) {
      setFormError("The action item needs some text.");
      return;
    }
    setFormError(null);
    update.mutate(
      {
        itemId: item.id,
        edits: { text: text.trim(), owner: owner.trim() || null, due_date: dueDate || null, status },
      },
      { onSuccess: () => setEditing(false) },
    );
  }

  function toggleDone(checked: boolean) {
    update.mutate({ itemId: item.id, edits: { status: checked ? "done" : "to do" } });
  }

  function handleDelete() {
    if (!window.confirm(`Delete the action item "${item.text}"?`)) return;
    remove.mutate(item.id);
  }

  if (editing) {
    return (
      <li>
        <form className="item-form" onSubmit={save}>
          <label>
            Action
            <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} />
          </label>
          <label>
            Owner
            <input value={owner} onChange={(e) => setOwner(e.target.value)} maxLength={100} placeholder="Not stated" />
          </label>
          <label>
            Due date
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </label>
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          {formError && <p role="alert" className="error">{formError}</p>}
          {update.isError && <p role="alert" className="error">{errorText(update.error, "Could not save")}</p>}
          <div className="button-row">
            <button type="submit" disabled={busy}>
              {update.isPending ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setEditing(false)} disabled={busy}>
              Cancel
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className="action-row">
      <input
        type="checkbox"
        checked={item.status === "done"}
        onChange={(e) => toggleDone(e.target.checked)}
        disabled={busy}
        aria-label={`Mark "${item.text}" as done`}
      />
      <div className="action-body">
        <span className={item.status === "done" ? "done-text" : undefined}>{item.text}</span>
        {item.source_line !== null && (
          <div>
            <Link
              to={`/meetings/${meetingId}#transcript-line-${item.source_line}`}
              onClick={onSourceClick}
            >
              Transcript line {item.source_line}
            </Link>
          </div>
        )}
        <span className="muted">
          {" "}· Owner: {item.owner ?? "not stated"} · Due: {item.due_date ?? "not stated"} · {item.status}
        </span>
        {update.isError && !editing && (
          <p role="alert" className="error">{errorText(update.error, "Could not update")}</p>
        )}
        {remove.isError && <p role="alert" className="error">{errorText(remove.error, "Could not delete")}</p>}
      </div>
      <div className="button-row">
        <button type="button" onClick={startEditing} disabled={busy}>
          Edit
        </button>
        <button type="button" className="danger" onClick={handleDelete} disabled={busy}>
          Delete
        </button>
      </div>
    </li>
  );
}

function AddActionItem({ meetingId }: { meetingId: number }) {
  const add = useAddActionItem(meetingId);
  const [text, setText] = useState("");
  const [owner, setOwner] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (add.isPending) return;
    if (!text.trim()) {
      setFormError("Write what needs to be done.");
      return;
    }
    setFormError(null);
    add.mutate(
      { text: text.trim(), owner: owner.trim() || null, due_date: dueDate || null, status: "to do" },
      {
        onSuccess: () => {
          setText("");
          setOwner("");
          setDueDate("");
        },
      },
    );
  }

  return (
    <form className="item-form add-item" onSubmit={submit}>
      <h3>Add an action item</h3>
      <label>
        Action
        <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} />
      </label>
      <label>
        Owner
        <input value={owner} onChange={(e) => setOwner(e.target.value)} maxLength={100} placeholder="Not stated" />
      </label>
      <label>
        Due date
        <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
      </label>
      {formError && <p role="alert" className="error">{formError}</p>}
      {add.isError && <p role="alert" className="error">{errorText(add.error, "Could not add the item")}</p>}
      <div className="button-row">
        <button type="submit" disabled={add.isPending}>
          {add.isPending ? "Adding…" : "Add action item"}
        </button>
      </div>
    </form>
  );
}



