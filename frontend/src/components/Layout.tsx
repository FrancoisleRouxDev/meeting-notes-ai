import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../auth";
import ThemeToggle from "./ThemeToggle";

export default function Layout() {
  const { data: user } = useMe();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const logout = useMutation({
    mutationFn: () => api<void>("/auth/logout", { method: "POST" }),
    onSettled: () => {
      // Clear cached meetings so the next person to log in can't see them.
      queryClient.clear();
      queryClient.setQueryData(["me"], null);
      navigate("/login", { replace: true });
    },
  });

  return (
    <>
      <header className="topbar">
        <Link to="/meetings" className="brand">
          <span className="brand-mark" aria-hidden="true">m</span>
          <span>meeting<span className="brand-light">notes</span></span>
          <span className="brand-ai">AI</span>
        </Link>
        <nav aria-label="Application navigation">
          <NavLink to="/meetings">Meetings</NavLink>
          <NavLink to="/calendar">Calendar</NavLink>
          <NavLink to="/meetings/new">New meeting</NavLink>
          <NavLink to="/items">Open items</NavLink>
          <NavLink to="/account">Account</NavLink>
        </nav>
        <span className="muted">{user?.email}</span>
        <ThemeToggle />
        <button onClick={() => logout.mutate()} disabled={logout.isPending}>
          Log out
        </button>
      </header>
      <Outlet />
    </>
  );
}
