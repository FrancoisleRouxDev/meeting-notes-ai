import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { CalendarView } from "./CalendarPage";

describe("CalendarView", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 25, 12));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows meetings and overdue action items with links to their source meeting", () => {
    render(
      <MemoryRouter>
        <CalendarView
          meetings={[
            {
              id: 7,
              title: "Vendor review",
              meeting_date: "2026-11-25",
              created_at: "2026-11-25T10:00:00",
            },
          ]}
          items={[
            {
              id: 3,
              text: "Send the contract",
              owner: "Alex",
              due_date: "2026-11-20",
              source_line: 4,
              status: "to do",
              meeting_id: 7,
              meeting_title: "Vendor review",
            },
          ]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "November 2026" })).toBeTruthy();
    const calendarDate = new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
    }).format(new Date(2026, 10, 25, 12));
    expect(screen.getByRole("link", { name: `Add meeting on ${calendarDate}` }).getAttribute("href"))
      .toBe("/meetings/new?date=2026-11-25");
    expect(screen.getByRole("link", { name: "Meeting: Vendor review" }).getAttribute("href"))
      .toBe("/meetings/7");
    const overdueItem = screen.getByRole("link", { name: "Overdue action item: Send the contract" });
    expect(overdueItem.getAttribute("href")).toBe("/meetings/7#transcript-line-4");
    expect(overdueItem.classList.contains("overdue")).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Next month" }));
    expect(screen.getByRole("heading", { name: "December 2026" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Previous month" }));
    expect(screen.getByRole("heading", { name: "November 2026" })).toBeTruthy();
  });
});
