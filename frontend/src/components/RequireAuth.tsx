import { type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

// Where to go back to after logging in. The full location is kept so
// navigation state (e.g. the selected train on /book) survives.
export interface LoginRedirectState {
  from?: {
    pathname: string;
    search: string;
    state: unknown;
  };
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <section className="booking-page">
        <p className="status-message">Checking your login...</p>
      </section>
    );
  }

  if (!user) {
    const state: LoginRedirectState = {
      from: {
        pathname: location.pathname,
        search: location.search,
        state: location.state,
      },
    };

    return <Navigate to="/login" state={state} replace />;
  }

  return children;
}

export default RequireAuth;
