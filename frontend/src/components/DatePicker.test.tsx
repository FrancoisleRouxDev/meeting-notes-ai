import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DatePicker } from "./DatePicker";

afterEach(cleanup);

describe("DatePicker", () => {
  it("opens on the selected month and updates the chosen date", () => {
    const onChange = vi.fn();
    render(<DatePicker label="Meeting date" value="2026-11-25" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: /Meeting date/ }));
    expect(screen.getByRole("dialog", { name: "Choose meeting date" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "November 2026" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Next month" }));
    expect(screen.getByRole("heading", { name: "December 2026" })).toBeTruthy();
    const targetLabel = new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(2026, 11, 1, 12));
    fireEvent.click(screen.getByRole("button", { name: targetLabel }));

    expect(onChange).toHaveBeenCalledWith("2026-12-01");
    expect(screen.getByRole("button", { name: /Meeting date/ }).getAttribute("aria-expanded"))
      .toBe("false");
  });

  it("closes the picker on Escape", () => {
    render(<DatePicker label="Meeting date" value="2026-11-25" onChange={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /Meeting date/ }));
    fireEvent.keyDown(document, { key: "Escape" });

    expect(screen.queryByRole("dialog", { name: "Choose meeting date" })).toBeNull();
  });
});
