import { useRef, useState, type DragEvent, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { DatePicker } from "../components/DatePicker";
import { dateKey, parseDateKey } from "../calendarDates";
import { useCreateMeeting, useUploadMeeting } from "../meetings";

export default function NewMeetingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const createMeeting = useCreateMeeting();
  const uploadMeeting = useUploadMeeting();

  const [title, setTitle] = useState("");
  const [meetingDate, setMeetingDate] = useState(() => {
    const requestedDate = parseDateKey(new URLSearchParams(location.search).get("date"));
    return dateKey(requestedDate ?? new Date());
  });
  const [transcript, setTranscript] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const dragDepth = useRef(0);

  const busy = createMeeting.isPending || uploadMeeting.isPending;
  const serverError = createMeeting.error ?? uploadMeeting.error;

  function selectFile(nextFile: File | null) {
    if (!nextFile) return;

    const extension = nextFile.name.split(".").pop()?.toLowerCase();
    if (!extension || !["txt", "vtt", "md"].includes(extension)) {
      setFile(null);
      setFormError("Choose a .txt, .vtt or .md transcript file.");
      if (fileInput.current) fileInput.current.value = "";
      return;
    }

    setFile(nextFile);
    setFormError(null);
  }

  function containsFiles(event: DragEvent<HTMLDivElement>) {
    return Array.from(event.dataTransfer.types).includes("Files") ||
      event.dataTransfer.files.length > 0;
  }

  function handleDragEnter(event: DragEvent<HTMLDivElement>) {
    if (!containsFiles(event)) return;
    event.preventDefault();
    dragDepth.current += 1;
    setIsDragging(true);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    if (!containsFiles(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    if (!containsFiles(event)) return;
    event.preventDefault();
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setIsDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    dragDepth.current = 0;
    setIsDragging(false);

    const droppedFiles = Array.from(event.dataTransfer.files);
    if (droppedFiles.length === 0) return;
    if (droppedFiles.length > 1) {
      setFile(null);
      setFormError("Drop one transcript file at a time.");
      if (fileInput.current) fileInput.current.value = "";
      return;
    }

    selectFile(droppedFiles[0]);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;

    if (!title.trim()) {
      setFormError("Enter a title for the meeting.");
      return;
    }
    setFormError(null);

    const onSuccess = (meeting: { id: number }) => navigate(`/meetings/${meeting.id}`);

    // A chosen file takes priority over pasted text.
    if (file) {
      uploadMeeting.mutate({ title, meeting_date: meetingDate, file }, { onSuccess });
    } else {
      createMeeting.mutate(
        { title, meeting_date: meetingDate, transcript: transcript.trim() || undefined },
        { onSuccess },
      );
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
        <DatePicker label="Meeting date" value={meetingDate} onChange={setMeetingDate} />
        <p className="muted">
          You can add a transcript now or attach one later from the meeting page.
        </p>
        <label>
          Transcript
          <textarea
            rows={12}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Paste the transcript here"
          />
        </label>
        <div
          className={`transcript-dropzone${isDragging ? " is-dragging" : ""}`}
          role="region"
          aria-label="Transcript file drop zone"
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p>Drop one transcript file here, or choose it below.</p>
          <label>
            Choose a file (.txt, .vtt, .md)
            <input
              ref={fileInput}
              type="file"
              accept=".txt,.vtt,.md"
              onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <p className="upload-hint">The file replaces pasted text when you save.</p>
          {file && (
            <div className="selected-file" role="status">
              <span>Selected: {file.name}</span>
              <button
                type="button"
                className="button-quiet file-remove"
                onClick={() => {
                  setFile(null);
                  if (fileInput.current) fileInput.current.value = "";
                }}
              >
                Remove
              </button>
            </div>
          )}
        </div>

        {formError && <p role="alert" className="error">{formError}</p>}
        {serverError && <p role="alert" className="error">{serverError.message}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : "Save meeting"}
        </button>
      </form>
    </main>
  );
}
