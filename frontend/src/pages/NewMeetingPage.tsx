import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateMeeting, useUploadMeeting } from "../meetings";

export default function NewMeetingPage() {
  const navigate = useNavigate();
  const createMeeting = useCreateMeeting();
  const uploadMeeting = useUploadMeeting();

  const [title, setTitle] = useState("");
  // Uses the local date, so "today" in the form matches the user's calendar.
  const [meetingDate, setMeetingDate] = useState(() => new Date().toLocaleDateString("en-CA"));
  const [transcript, setTranscript] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const busy = createMeeting.isPending || uploadMeeting.isPending;
  const serverError = createMeeting.error ?? uploadMeeting.error;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;

    if (!title.trim()) {
      setFormError("Enter a title for the meeting.");
      return;
    }
    if (!file && !transcript.trim()) {
      setFormError("Paste a transcript or choose a file.");
      return;
    }
    setFormError(null);

    const onSuccess = (meeting: { id: number }) => navigate(`/meetings/${meeting.id}`);

    // A chosen file takes priority over pasted text.
    if (file) {
      uploadMeeting.mutate({ title, meeting_date: meetingDate, file }, { onSuccess });
    } else {
      createMeeting.mutate({ title, meeting_date: meetingDate, transcript }, { onSuccess });
    }
  }

  return (
    <main>
      <h1>New meeting</h1>
      <form onSubmit={handleSubmit} noValidate>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
        </label>
        <label>
          Meeting date
          <input type="date" value={meetingDate} onChange={(e) => setMeetingDate(e.target.value)} />
        </label>
        <label>
          Transcript
          <textarea
            rows={12}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste the transcript here"
          />
        </label>
        <label>
          Or upload a file (.txt, .vtt, .md). A chosen file is used instead of pasted text.
          <input
            type="file"
            accept=".txt,.vtt,.md"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        {formError && <p role="alert" className="error">{formError}</p>}
        {serverError && <p role="alert" className="error">{serverError.message}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Save meeting"}
        </button>
      </form>
    </main>
  );
}
