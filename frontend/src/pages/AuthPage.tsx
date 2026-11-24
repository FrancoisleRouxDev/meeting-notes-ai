import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { User } from "../auth";

type Props = { mode: "login" | "register" };

export default function AuthPage({ mode }: Props) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const isRegister = mode === "register";

  const submit = useMutation({
    mutationFn: () =>
      api<User>(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    onSuccess: (user) => {
      queryClient.setQueryData(["me"], user);
      navigate("/meetings", { replace: true });
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    // Ignore extra clicks while a request is running.
    if (submit.isPending) return;
    submit.mutate();
  }

  return (
    <main>
      <h1>{isRegister ? "Create account" : "Log in"}</h1>
      <form onSubmit={handleSubmit} noValidate>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isRegister ? "new-password" : "current-password"}
            required
          />
        </label>
        {submit.isError && (
          <p role="alert" className="error">
            {submit.error.message}
          </p>
        )}
        <button type="submit" disabled={submit.isPending}>
          {submit.isPending ? "Please wait…" : isRegister ? "Create account" : "Log in"}
        </button>
      </form>
      <p>
        {isRegister ? (
          <>
            Already have an account? <Link to="/login">Log in</Link>
          </>
        ) : (
          <>
            No account yet? <Link to="/register">Register</Link>
            <br />
            <Link to="/forgot-password">Forgot password?</Link>
          </>
        )}
      </p>
    </main>
  );
}