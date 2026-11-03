import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getMyBookings, type BookingListItem } from "../api";
import { formatJourneyDate, STATUS_CLASS } from "../format";

function MyBookingsPage() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<BookingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reference, setReference] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getMyBookings()
      .then((result) => {
        if (!cancelled) {
          setBookings(result);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadError(
            err instanceof Error ? err.message : "Failed to load bookings.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = reference.trim().toUpperCase();

    if (!trimmed) {
      setError("Enter your booking reference.");
      return;
    }

    navigate(`/booking/${encodeURIComponent(trimmed)}`);
  }

  return (
    <section className="booking-page">
      <h1>My bookings</h1>

      {loading && <p className="status-message">Loading your bookings...</p>}

      {loadError && <p className="error-message">{loadError}</p>}

      {!loading && !loadError && bookings.length === 0 && (
        <p className="status-message">
          You have no bookings yet. <Link to="/">Search for a train</Link>.
        </p>
      )}

      {bookings.length > 0 && (
        <ul className="booking-list">
          {bookings.map((booking) => (
            <li key={booking.booking_reference}>
              <Link to={`/booking/${booking.booking_reference}`}>
                <div>
                  <strong>
                    {booking.train.name} ({booking.train.train_number})
                  </strong>
                  <span>
                    {booking.source_code} → {booking.destination_code} ·{" "}
                    {formatJourneyDate(booking.journey_date)} ·{" "}
                    {booking.coach_class} · {booking.passenger_count} passenger
                    {booking.passenger_count === 1 ? "" : "s"}
                  </span>
                  <span>
                    {booking.booking_reference} · ₹{booking.total_amount}
                  </span>
                </div>
                <span
                  className={`status-pill ${STATUS_CLASS[booking.status] ?? ""}`}
                >
                  {booking.status}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <h2 className="section-heading">Find a booking by reference</h2>

      <form className="search-card lookup-card" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="reference">Booking reference</label>
          <input
            id="reference"
            value={reference}
            maxLength={20}
            placeholder="e.g. 3F9A1C0B7D2E4A6F8B1C"
            onChange={(event) => setReference(event.target.value)}
          />
        </div>

        {error && <p className="error-message">{error}</p>}

        <button className="search-button" type="submit">
          View booking
        </button>
      </form>
    </section>
  );
}

export default MyBookingsPage;
