import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { cancelBooking, getBooking, type BookingDetails } from "../api";
import { BERTH_LABELS, formatJourneyDate, formatTime } from "../format";

const STATUS_CLASS: Record<string, string> = {
  CONFIRMED: "status-confirmed",
  PENDING: "status-pending",
  CANCELLED: "status-closed",
  EXPIRED: "status-closed",
};

function BookingDetailsPage() {
  const { reference = "" } = useParams();
  const [booking, setBooking] = useState<BookingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getBooking(reference)
      .then((result) => {
        if (!cancelled) {
          setBooking(result);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load booking.",
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
  }, [reference]);

  async function handleCancel() {
    if (
      !booking ||
      !window.confirm(
        "Cancel this booking for all passengers? This cannot be undone.",
      )
    ) {
      return;
    }

    setCancelError("");
    setCancelling(true);

    try {
      setBooking(await cancelBooking(booking.booking_reference));
    } catch (err: unknown) {
      setCancelError(
        err instanceof Error ? err.message : "Failed to cancel booking.",
      );
    } finally {
      setCancelling(false);
    }
  }

  return (
    <section className="booking-page">
      <Link className="link-button" to="/booking">
        ← Find another booking
      </Link>

      <h1>Booking details</h1>

      {loading && <p className="status-message">Loading booking...</p>}

      {error && <p className="error-message">{error}</p>}

      {booking && (
        <article className="train-card">
          <div className="train-heading">
            <div>
              <h3>{booking.train.name}</h3>
              <span className="train-number">
                Train no. {booking.train.train_number}
              </span>
            </div>
            <span
              className={`status-pill ${STATUS_CLASS[booking.status] ?? ""}`}
            >
              {booking.status}
            </span>
          </div>

          <div className="journey-times">
            <div>
              <strong>{booking.source.departure_time ?? "N/A"}</strong>
              <p>{booking.source.name}</p>
              <span>{booking.source.code}</span>
            </div>

            <div className="journey-arrow" aria-hidden="true">
              ───→
            </div>

            <div className="destination-time">
              <strong>{booking.destination.arrival_time ?? "N/A"}</strong>
              <p>{booking.destination.name}</p>
              <span>{booking.destination.code}</span>
            </div>
          </div>

          <section className="booking-result">
            <p className="booking-meta">
              Booking reference <strong>{booking.booking_reference}</strong>
            </p>
            <p className="booking-meta">
              Class <strong>{booking.coach_class}</strong> · Journey date{" "}
              <strong>{formatJourneyDate(booking.journey_date)}</strong>
              {booking.distance_km && <> · {booking.distance_km} km</>}
            </p>
            <p className="booking-meta">
              Total <strong>₹{booking.total_amount}</strong>
            </p>

            {booking.status === "PENDING" && (
              <p className="booking-notice">
                This booking is not confirmed yet. The seat hold expires at{" "}
                <strong>{formatTime(booking.expires_at)}</strong>.
              </p>
            )}

            {booking.status === "CANCELLED" && (
              <p className="booking-notice booking-notice-expired">
                This booking has been cancelled and its seats released.
              </p>
            )}

            {booking.status === "EXPIRED" && (
              <p className="booking-notice booking-notice-expired">
                The seat hold expired before the booking was confirmed.
              </p>
            )}

            <ul className="booked-passengers">
              {booking.passengers.map((passenger, index) => (
                <li key={index}>
                  <span>
                    {passenger.passenger_name} ({passenger.age},{" "}
                    {passenger.gender.toLowerCase()})
                  </span>
                  <strong>
                    {passenger.seat_number
                      ? `${passenger.coach_number} / ${passenger.seat_number} ${
                          BERTH_LABELS[passenger.berth_type ?? ""] ??
                          passenger.berth_type
                        }`
                      : booking.status === "PENDING"
                        ? "Pending"
                        : "—"}
                  </strong>
                </li>
              ))}
            </ul>

            {cancelError && <p className="error-message">{cancelError}</p>}

            {booking.can_cancel && (
              <button
                type="button"
                className="danger-button"
                onClick={handleCancel}
                disabled={cancelling}
              >
                {cancelling ? "Cancelling..." : "Cancel booking"}
              </button>
            )}
          </section>
        </article>
      )}
    </section>
  );
}

export default BookingDetailsPage;
