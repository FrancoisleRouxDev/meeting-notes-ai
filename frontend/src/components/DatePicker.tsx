import { useEffect, useId, useRef, useState } from "react";
import { dateKey, monthGridDays, parseDateKey } from "../calendarDates";

const weekdayFormatter = new Intl.DateTimeFormat(undefined, { weekday: "short" });
const monthFormatter = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });
const dateFormatter = new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
  year: "numeric",
});
const displayDateFormatter = new Intl.DateTimeFormat(undefined, {
  month: "long",
  day: "numeric",
  year: "numeric",
});
const weekdays = Array.from({ length: 7 }, (_, index) =>
  weekdayFormatter.format(new Date(2026, 10, 23 + index, 12)),
);

function monthStart(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1, 12);
}

export function DatePicker({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [today] = useState(() => new Date());
  const selectedDate = parseDateKey(value) ?? today;
  const id = useId();
  const [month, setMonth] = useState(() => monthStart(selectedDate));
  const [isOpen, setIsOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const todayKey = dateKey(today);
  const selectedKey = dateKey(selectedDate);
  const monthLabel = monthFormatter.format(month);

  useEffect(() => {
    if (!isOpen) return;

    function closeOutside(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node)) setIsOpen(false);
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        trigger.current?.focus();
      }
    }

    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isOpen]);

  function shiftMonth(amount: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + amount, 1, 12));
  }

  function selectDate(date: Date) {
    onChange(dateKey(date));
    setMonth(monthStart(date));
    setIsOpen(false);
  }

  function selectToday() {
    const today = new Date();
    selectDate(today);
  }

  return (
    <div className="date-picker" ref={root}>
      <span className="date-picker-label" id={`${id}-label`}>{label}</span>
      <button
        type="button"
        ref={trigger}
        className="date-picker-trigger"
        aria-labelledby={`${id}-label ${id}-value`}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        <span id={`${id}-value`}>{displayDateFormatter.format(selectedDate)}</span>
        <span className="date-picker-trigger-icon" aria-hidden="true">▾</span>
      </button>
      {isOpen && (
        <div className="date-picker-popover" role="dialog" aria-label="Choose meeting date">
          <div className="date-picker-toolbar">
            <button type="button" className="date-picker-nav" aria-label="Previous month" onClick={() => shiftMonth(-1)}>
              ‹
            </button>
            <h2 aria-live="polite">{monthLabel}</h2>
            <button type="button" className="date-picker-nav" aria-label="Next month" onClick={() => shiftMonth(1)}>
              ›
            </button>
          </div>
          <div className="date-picker-weekdays" aria-hidden="true">
            {weekdays.map((weekday, index) => <span key={`${weekday}-${index}`}>{weekday}</span>)}
          </div>
          <div className="date-picker-grid">
            {monthGridDays(month).map((day) => {
              const key = dateKey(day);
              const isSelected = key === selectedKey;
              const isToday = key === todayKey;
              const isOutsideMonth = day.getMonth() !== month.getMonth();
              const className = [
                "date-picker-day",
                isSelected ? "is-selected" : "",
                isToday ? "is-today" : "",
                isOutsideMonth ? "is-outside-month" : "",
              ].filter(Boolean).join(" ");

              return (
                <button
                  type="button"
                  className={className}
                  key={key}
                  aria-label={dateFormatter.format(day)}
                  aria-pressed={isSelected}
                  aria-current={isToday ? "date" : undefined}
                  onClick={() => selectDate(day)}
                >
                  {day.getDate()}
                </button>
              );
            })}
          </div>
          <div className="date-picker-footer">
            <button type="button" className="button-quiet" onClick={selectToday}>Today</button>
          </div>
        </div>
      )}
    </div>
  );
}
