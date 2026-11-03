import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";
import RequireAuth from "./components/RequireAuth";
import AuthPage from "./pages/AuthPage";
import BookingDetailsPage from "./pages/BookingDetailsPage";
import BookingPage from "./pages/BookingPage";
import CancelTicketPage from "./pages/CancelTicketPage";
import ConfirmationPage from "./pages/ConfirmationPage";
import MyBookingsPage from "./pages/MyBookingsPage";
import SearchPage from "./pages/SearchPage";
import "./App.css";

function HeaderNav() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <nav className="header-nav">
      {user ? (
        <>
          <Link to="/booking">My bookings</Link>
          <Link to="/cancel">Cancel ticket</Link>
          <span className="header-label">{user.name}</span>
          <button
            type="button"
            className="link-button"
            onClick={handleLogout}
          >
            Log out
          </button>
        </>
      ) : (
        !loading && (
          <>
            <Link to="/login">Log in</Link>
            <Link to="/register">Register</Link>
            <span className="header-label">Train Booking System</span>
          </>
        )
      )}
    </nav>
  );
}

function App() {
  return (
    <main className="page">
      <header className="site-header">
        <Link className="brand" to="/">
          <span className="brand-icon">🚆</span>
          <span>Railway</span>
        </Link>
        <HeaderNav />
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route
          path="/book"
          element={
            <RequireAuth>
              <BookingPage />
            </RequireAuth>
          }
        />
        <Route
          path="/booking"
          element={
            <RequireAuth>
              <MyBookingsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/cancel"
          element={
            <RequireAuth>
              <CancelTicketPage />
            </RequireAuth>
          }
        />
        <Route
          path="/booking/confirmed"
          element={
            <RequireAuth>
              <ConfirmationPage />
            </RequireAuth>
          }
        />
        <Route
          path="/booking/:reference"
          element={
            <RequireAuth>
              <BookingDetailsPage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer className="site-footer">
        Built for your next railway journey.
      </footer>
    </main>
  );
}

export default App;
