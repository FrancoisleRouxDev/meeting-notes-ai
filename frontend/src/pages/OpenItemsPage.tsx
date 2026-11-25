import { useState } from "react";
import { Link } from "react-router-dom";
import { useOpenItems } from "../items";

export default function OpenItemsPage() {
  const [status, setStatus] = useState("");
  const [owner, setOwner] = useState("");
  const [overdue, setOverdue] = useState(false);
  const { data, isPending, isError, error } = useOpenItems({ status, owner, overdue });

  return (
    <main>
      <h1>My action items</h1>

      <div className="filters">
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Open (not done)</option>
            <option value="to do">To do</option>
            <option value="in progress">In progress</option>
            <option value="done">Done</option>
          </select>
        </label>

        <label>
          Owner
          <input
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
            placeholder="Any owner"
          />
        </label>

        <label className="checkbox">
          <input
            type="checkbox"
            checked={overdue}
            onChange={(e) => setOverdue(e.target.checked)}
          />
          Overdue only
        </label>
      </div>

      {isPending && <p>Loading items...</p>}

      {isError && (
        <p className="error" role="alert">
          {error instanceof Error ? error.message : "Could not load items"}
        </p>
      )}

      {data && data.length === 0 && <p>No items match these filters.</p>}

      {data && data.length > 0 && (
        <ul className="item-list">
          {data.map((item) => (
            <li key={item.id} className="item-card">
              <p className="item-text">{item.text}</p>
              <p className="muted">
                Owner: {item.owner ?? "not stated"} | Due: {item.due_date ?? "not stated"} |{" "}
                <span className="badge">{item.status}</span>
              </p>
              <Link
                to={`/meetings/${item.meeting_id}${
                  item.source_line === null ? "" : `#transcript-line-${item.source_line}`
                }`}
              >
                {item.source_line === null
                  ? item.meeting_title
                  : `${item.meeting_title} · Transcript line ${item.source_line}`}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
