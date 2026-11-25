import { useState, type InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: string };

function EyeIcon({ open }: { open: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
      <circle cx="12" cy="12" r="3" />
      {!open && <line x1="3" y1="3" x2="21" y2="21" />}
    </svg>
  );
}

export default function PasswordInput({ label, ...inputProps }: Props) {
  const [visible, setVisible] = useState(false);
  return (
    <label>
      {label}
      <div className="password-field">
        <input {...inputProps} type={visible ? "text" : "password"} />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
        >
          <EyeIcon open={visible} />
        </button>
      </div>
    </label>
  );
}