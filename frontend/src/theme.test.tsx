import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import ThemeToggle from "./components/ThemeToggle";
import { ThemeProvider } from "./theme";

describe("ThemeToggle", () => {
  beforeEach(() => {
    window.localStorage.setItem("meeting-notes-theme", "light");
    delete document.documentElement.dataset.theme;
  });

  it("toggles the color scheme and remembers the selection", () => {
    const view = render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("meeting-notes-theme")).toBe("dark");

    view.unmount();
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );

    expect(screen.getByRole("button", { name: "Switch to light mode" }).getAttribute("aria-pressed"))
      .toBe("true");
  });
});
