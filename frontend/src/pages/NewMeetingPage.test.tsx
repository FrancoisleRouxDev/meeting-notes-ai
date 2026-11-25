import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import NewMeetingPage from "./NewMeetingPage";

afterEach(cleanup);

function renderNewMeeting(initialEntry = "/meetings/new") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <NewMeetingPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("NewMeetingPage transcript drop zone", () => {
  it("prefills the date selected from the calendar", () => {
    renderNewMeeting("/meetings/new?date=2026-11-25");

    fireEvent.click(screen.getByRole("button", { name: /Meeting date/ }));
    const targetLabel = new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(2026, 10, 25, 12));

    expect(screen.getByRole("button", { name: targetLabel }).getAttribute("aria-pressed"))
      .toBe("true");
  });

  it("accepts supported transcript files dropped onto the drop zone", () => {
    renderNewMeeting();
    const file = new File(["Transcript"], "weekly-sync.vtt", { type: "text/vtt" });

    fireEvent.drop(screen.getByRole("region", { name: "Transcript file drop zone" }), {
      dataTransfer: { files: [file], types: ["Files"] },
    });

    expect(screen.getByRole("status").textContent).toContain("weekly-sync.vtt");
    expect(screen.getByLabelText("Choose a file (.txt, .vtt, .md)").getAttribute("type"))
      .toBe("file");
  });

  it("rejects unsupported files and multiple dropped files", () => {
    renderNewMeeting();
    const dropZone = screen.getByRole("region", { name: "Transcript file drop zone" });

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [new File(["data"], "agenda.pdf", { type: "application/pdf" })],
        types: ["Files"],
      },
    });
    expect(screen.getByRole("alert").textContent).toContain(".txt, .vtt or .md");

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [
          new File(["one"], "one.txt", { type: "text/plain" }),
          new File(["two"], "two.txt", { type: "text/plain" }),
        ],
        types: ["Files"],
      },
    });
    expect(screen.getByRole("alert").textContent).toContain("one transcript file at a time");
  });
});
