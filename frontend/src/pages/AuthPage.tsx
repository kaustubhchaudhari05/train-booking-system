import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { type LoginRedirectState } from "../components/RequireAuth";

const MIN_PASSWORD_LENGTH = 8;

const ICON_PROPS = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
} as const;

function EyeIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg {...ICON_PROPS}>
      <path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a17.6 17.6 0 0 1-2.9 3.9" />
      <path d="M6.6 6.6A17.4 17.4 0 0 0 2 12s3.5 7 10 7a10.4 10.4 0 0 0 5.4-1.6" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
      <path d="M2 2l20 20" />
    </svg>
  );
}

interface AuthPageProps {
  mode: "login" | "register";
}

// Login and registration share one form; registration adds the name.
function AuthPage({ mode }: AuthPageProps) {
  const { user, loading, login, register } = useAuth();
  const navigate = useNavigate();
  const redirect = (useLocation().state as LoginRedirectState | null)?.from;

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const isRegister = mode === "register";

  function goBack() {
    if (redirect) {
      navigate(`${redirect.pathname}${redirect.search}`, {
        state: redirect.state,
        replace: true,
      });
    } else {
      navigate("/", { replace: true });
    }
  }

  // Already logged in (e.g. opened /login directly).
  if (!loading && user && !submitting) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (isRegister && !name.trim()) {
      setError("Enter your name.");
      return;
    }

    if (!email.trim()) {
      setError("Enter your email address.");
      return;
    }

    if (isRegister && password.length < MIN_PASSWORD_LENGTH) {
      setError(
        `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`,
      );
      return;
    }

    if (!password) {
      setError("Enter your password.");
      return;
    }

    setSubmitting(true);

    try {
      if (isRegister) {
        await register(name.trim(), email.trim(), password);
      } else {
        await login(email.trim(), password);
      }

      goBack();
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : isRegister
            ? "Failed to create your account."
            : "Failed to log in.",
      );
      setSubmitting(false);
    }
  }

  return (
    <section className="booking-page">
      <h1>{isRegister ? "Create an account" : "Log in"}</h1>

      {redirect && (
        <p className="cancel-help">
          {isRegister ? "Create an account" : "Log in"} to continue.
        </p>
      )}

      <form
        className="search-card lookup-card"
        onSubmit={handleSubmit}
        noValidate
      >
        {isRegister && (
          <div className="form-field">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              value={name}
              maxLength={100}
              autoComplete="name"
              onChange={(event) => setName(event.target.value)}
            />
          </div>
        )}

        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            maxLength={255}
            autoComplete="email"
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>

        <div className="form-field">
          <label htmlFor="password">Password</label>
          <div className="password-field">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              maxLength={128}
              autoComplete={isRegister ? "new-password" : "current-password"}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              className="password-toggle"
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              onClick={() => setShowPassword((shown) => !shown)}
            >
              {showPassword ? <EyeOffIcon /> : <EyeIcon />}
            </button>
          </div>
        </div>

        {error && <p className="error-message">{error}</p>}

        <button className="search-button" type="submit" disabled={submitting}>
          {submitting
            ? isRegister
              ? "Creating account..."
              : "Logging in..."
            : isRegister
              ? "Create account"
              : "Log in"}
        </button>

        <p className="status-message">
          {isRegister ? "Already have an account? " : "New here? "}
          <Link
            className="link-button"
            to={isRegister ? "/login" : "/register"}
            state={redirect ? { from: redirect } : undefined}
            replace
          >
            {isRegister ? "Log in" : "Create an account"}
          </Link>
        </p>
      </form>
    </section>
  );
}

export default AuthPage;
