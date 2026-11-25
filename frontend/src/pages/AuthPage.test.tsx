import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api";
import AuthPage from "./AuthPage";
import { ThemeProvider } from "../theme";

vi.mock("../api", () => ({ api: vi.fn() }));

function renderLogin() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <AuthPage mode="login" />
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

describe("AuthPage", () => {
  beforeEach(() => {
    vi.mocked(api).mockReset();
  });

  it("shows failed sign-in feedback inline", async () => {
    vi.mocked(api).mockRejectedValue(new Error("Invalid email or password"));
    renderLogin();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "person@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Invalid email or password");
    await waitFor(() => expect(api).toHaveBeenCalledOnce());
  });
});
