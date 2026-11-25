import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import LandingPage from "./LandingPage";
import { ThemeProvider } from "../theme";

describe("LandingPage", () => {
  it("explains the product and offers a route to get started", () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      </ThemeProvider>,
    );

    expect(
      screen.getByRole("heading", { name: /good meetings deserve great follow-through/i }),
    ).toBeTruthy();
    expect(
      screen.getByText(/turn a meeting transcript into a clear summary/i),
    ).toBeTruthy();
    expect(screen.getAllByRole("link", { name: /try it free|get started/i })).toHaveLength(2);
    expect(screen.getByRole("heading", { name: /from conversation to clear next steps/i }))
      .toBeTruthy();
  });
});
