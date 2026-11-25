import { useState } from "react";
import { Link } from "react-router-dom";
import { useOpenItems, type OpenItem } from "../items";
import { useMeetings, type MeetingSummary } from "../meetings";
import { dateKey, monthGridDays } from "../calendarDates";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function CalendarPage() {
  const meetings = useMeetings();
  const items = useOpenItems({ status: "", owner: "", overdue: false });

  if (meetings.isError || items.isError) {
    const error = meetings.error ?? items.error;
    return (
      <main className="calendar-page">
        <h1>Calendar</h1>
        <p className="error" role="alert">
          Couldn&apos;t load calendar data: {error instanceof Error ? error.message : "Please try again."}
        </p>
      </main>
    );
  }

  if (meetings.isPending || items.isPending) {
    return (
      <main className="calendar-page">
        <h1>Calendar</h1>
        <p role="status">Loading your calendar…</p>
      </main>
    );
  }

  return <CalendarView meetings={meetings.data} items={items.data} />;
}

export function CalendarView({ meetings, items }: { meetings: MeetingSummary[]; items: OpenItem[] }) {
  const [month, setMonth] = useState(() => {
    const today = new Date();
    return new Date(today.getFullYear(), today.getMonth(), 1);
  });
  const [todayKey] = useState(() => dateKey(new Date()));
  const days = monthGridDays(month);
  const monthLabel = new Intl.DateTimeFormat(undefined, {
    month: "long",
    year: "numeric",
  }).format(month);
  const longDate = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  const meetingsByDate = new Map<string, MeetingSummary[]>();
  for (const meeting of meetings) {
    const dayMeetings = meetingsByDate.get(meeting.meeting_date) ?? [];
    dayMeetings.push(meeting);
    meetingsByDate.set(meeting.meeting_date, dayMeetings);
  }

  const itemsByDate = new Map<string, Array<{ item: OpenItem; dueDate: string }>>();
  for (const item of items) {
    const dueDate = item.due_date;
    if (!dueDate) continue;
    const dayItems = itemsByDate.get(dueDate) ?? [];
    dayItems.push({ item, dueDate });
    itemsByDate.set(dueDate, dayItems);
  }

  function shiftMonth(amount: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + amount, 1));
  }

  function goToToday() {
    const today = new Date();
    setMonth(new Date(today.getFullYear(), today.getMonth(), 1));
  }

  return (
    <main className="calendar-page">
      <div className="calendar-heading">
        <div>
          <h1>Calendar</h1>
          <p className="muted">
            Meetings appear on their meeting date; open action items appear on their due date.
            Use + on a day to add a meeting, with a transcript now or later.
          </p>
        </div>
        <Link className="button" to="/meetings/new">Add a meeting</Link>
      </div>

      <div className="calendar-toolbar">
        <button
          type="button"
          className="calendar-nav"
          aria-label="Previous month"
          onClick={() => shiftMonth(-1)}
        >
          ‹
        </button>
        <h2 aria-live="polite">{monthLabel}</h2>
        <button
          type="button"
          className="calendar-nav"
          aria-label="Next month"
          onClick={() => shiftMonth(1)}
        >
          ›
        </button>
        <button type="button" className="button-quiet calendar-today" onClick={goToToday}>
          Today
        </button>
      </div>

      <div className="calendar-scroll" role="region" aria-label={`${monthLabel} calendar`} tabIndex={0}>
        <div className="calendar-weekdays" aria-hidden="true">
          {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday}</span>)}
        </div>
        <div className="calendar-grid">
          {days.map((day) => {
            const key = dateKey(day);
            const dayMeetings = meetingsByDate.get(key) ?? [];
            const dayItems = itemsByDate.get(key) ?? [];
            const isCurrentMonth = day.getMonth() === month.getMonth();
            const isToday = key === todayKey;
            const className = [
              "calendar-day",
              isCurrentMonth ? "" : "calendar-day--outside",
              isToday ? "calendar-day--today" : "",
            ].filter(Boolean).join(" ");

            return (
              <div
                className={className}
                key={key}
                role="group"
                aria-label={`${longDate.format(day)}${isToday ? ", today" : ""}`}
              >
                <div className="calendar-day-heading">
                  <time dateTime={key} aria-current={isToday ? "date" : undefined}>
                    {day.getDate()}
                  </time>
                  {isToday && <span className="calendar-today-label">Today</span>}
                  <Link
                    className="calendar-add"
                    to={`/meetings/new?date=${key}`}
                    aria-label={`Add meeting on ${longDate.format(day)}`}
                    title="Add a meeting on this date"
                  >
                    +
                  </Link>
                </div>
                <ul className="calendar-events">
                  {dayMeetings.map((meeting) => (
                    <li key={`meeting-${meeting.id}`}>
                      <Link
                        className="calendar-event meeting-event"
                        to={`/meetings/${meeting.id}`}
                        title={`Meeting: ${meeting.title}`}
                        aria-label={`Meeting: ${meeting.title}`}
                      >
                        <span className="calendar-event-title">{meeting.title}</span>
                        <span className="calendar-event-meta">Meeting</span>
                      </Link>
                    </li>
                  ))}
                  {dayItems.map(({ item, dueDate }) => {
                    const isOverdue = dueDate < todayKey;
                    const source = item.source_line === null
                      ? ""
                      : `#transcript-line-${item.source_line}`;
                    return (
                      <li key={`item-${item.id}`}>
                        <Link
                          className={`calendar-event action-event${isOverdue ? " overdue" : ""}`}
                          to={`/meetings/${item.meeting_id}${source}`}
                          title={`Action item: ${item.text}`}
                          aria-label={`${isOverdue ? "Overdue" : "Due"} action item: ${item.text}`}
                        >
                          <span className="calendar-event-title">{item.text}</span>
                          <span className="calendar-event-meta">
                            {isOverdue ? "Overdue" : "Due"} · {item.owner ?? "Unassigned"}
                          </span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
