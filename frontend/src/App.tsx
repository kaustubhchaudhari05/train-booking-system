import { Link, Navigate, Route, Routes } from "react-router-dom";
import BookingDetailsPage from "./pages/BookingDetailsPage";
import BookingLookupPage from "./pages/BookingLookupPage";
import BookingPage from "./pages/BookingPage";
import ConfirmationPage from "./pages/ConfirmationPage";
import SearchPage from "./pages/SearchPage";
import "./App.css";

function App() {
  return (
    <main className="page">
      <header className="site-header">
        <Link className="brand" to="/">
          <span className="brand-icon">🚆</span>
          <span>Railway</span>
        </Link>
        <nav className="header-nav">
          <Link to="/booking">My booking</Link>
          <span className="header-label">Train Booking System</span>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/book" element={<BookingPage />} />
        <Route path="/booking" element={<BookingLookupPage />} />
        <Route path="/booking/confirmed" element={<ConfirmationPage />} />
        <Route path="/booking/:reference" element={<BookingDetailsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer className="site-footer">
        Built for your next railway journey.
      </footer>
    </main>
  );
}

export default App;
