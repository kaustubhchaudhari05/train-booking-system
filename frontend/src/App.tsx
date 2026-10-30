import { Link, Navigate, Route, Routes } from "react-router-dom";
import BookingPage from "./pages/BookingPage";
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
        <span className="header-label">Train Booking System</span>
      </header>

      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/book" element={<BookingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <footer className="site-footer">
        Built for your next railway journey.
      </footer>
    </main>
  );
}

export default App;
