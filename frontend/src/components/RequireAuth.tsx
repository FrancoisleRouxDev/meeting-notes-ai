import { Navigate, Outlet } from "react-router-dom";
import { useMe } from "../auth";

export default function RequireAuth() {
  const { data: user, isPending } = useMe();

  if (isPending) return <p role="status">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}