import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api";
import type { User } from "../auth";
import PasswordInput from "../components/PasswordInput";


type Props = { mode: "login" | "register" };

export default function AuthPage({ mode }: Props) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const isRegister = mode === "register";
  const passwordsDiffer = isRegister && confirm.length > 0 && password !== confirm;

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
    if (submit.isPending || passwordsDiffer) return;
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
        <PasswordInput
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={isRegister ? "new-password" : "current-password"}
          required
        />
        {isRegister && (
          <PasswordInput
            label="Confirm password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="new-password"
            required
          />
        )}
        {passwordsDiffer && <p className="error">The passwords do not match.</p>}
        {submit.isError && (
          <p role="alert" className="error">
            {submit.error.message}
          </p>
        )}
        <button type="submit" disabled={submit.isPending || passwordsDiffer}>
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