import { Link } from "react-router-dom";
import { useMeetings } from "../meetings";

export default function MeetingsPage() {
  const { data: meetings, isPending, isError, error } = useMeetings();

  return (
    <main>
      <h1>Meetings</h1>

      {isPending && <p role="status">Loading meetings…</p>}
      {isError && (
        <p role="alert" className="error">
          Couldn't load meetings: {error.message}
        </p>
      )}

      {meetings && meetings.length === 0 && (
        <p>
          No meetings yet. <Link to="/meetings/new">Add your first transcript</Link>.
        </p>
      )}

      {meetings && meetings.length > 0 && (
        <ul className="meeting-list">
          {meetings.map((meeting) => (
            <li key={meeting.id}>
              <Link to={`/meetings/${meeting.id}`}>{meeting.title}</Link>
              <span className="muted"> {meeting.meeting_date}</span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
