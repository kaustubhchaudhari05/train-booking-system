import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  confirmBooking,
  type BookingResult,
  type CoachClass,
  type TrainSearchResult,
} from "../api";
import { formatTime } from "../format";
import { type ConfirmationPageState } from "../pages/ConfirmationPage";

function secondsUntil(isoString: string | null) {
  if (!isoString) {
    return null;
  }

  return Math.max(
    0,
    Math.floor((new Date(isoString).getTime() - Date.now()) / 1000),
  );
}

function formatCountdown(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

interface PendingBookingProps {
  booking: BookingResult;
  train: TrainSearchResult;
  coachClass: CoachClass;
}

function PendingBooking({ booking, train, coachClass }: PendingBookingProps) {
  const navigate = useNavigate();
  const [secondsLeft, setSecondsLeft] = useState(() =>
    secondsUntil(booking.expires_at),
  );
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!booking.expires_at) {
      return;
    }

    const timer = window.setInterval(() => {
      setSecondsLeft(secondsUntil(booking.expires_at));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [booking.expires_at]);

  // The backend also rejects expired holds; this only keeps the UI honest.
  const expired = secondsLeft === 0;

  async function handleConfirm() {
    setError("");
    setConfirming(true);

    try {
      const confirmed = await confirmBooking(booking.booking_id);
      const state: ConfirmationPageState = {
        train,
        coachClass,
        booking: confirmed,
      };

      // Replace /book so browser back does not return to a stale form.
      navigate("/booking/confirmed", { state, replace: true });
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to confirm booking.",
      );
      setConfirming(false);
    }
  }

  return (
    <section className="booking-result" aria-live="polite">
      <h4>Booking pending confirmation</h4>

      {expired ? (
        <p className="booking-notice booking-notice-expired">
          The seat hold has expired. Go back to the results and book again.
        </p>
      ) : (
        <p className="booking-notice">
          Your booking is not confirmed yet. Seat numbers are shown after
          confirmation. Confirm before{" "}
          <strong>{formatTime(booking.expires_at)}</strong>
          {secondsLeft !== null && (
            <> ({formatCountdown(secondsLeft)} left)</>
          )}
          , or the booking will expire.
        </p>
      )}

      <p className="booking-meta">
        Booking reference <strong>{booking.booking_reference}</strong>
      </p>
      <p className="booking-meta">
        Status <strong>{expired ? "EXPIRED" : booking.status}</strong> · Total{" "}
        <strong>₹{booking.total_amount}</strong>
      </p>

      <ul className="booked-passengers">
        {booking.passengers.map((passenger, index) => (
          <li key={index}>
            <span>
              {passenger.passenger_name} ({passenger.age},{" "}
              {passenger.gender.toLowerCase()})
            </span>
            <strong>Pending</strong>
          </li>
        ))}
      </ul>

      {error && <p className="error-message">{error}</p>}

      <button
        className="search-button"
        type="button"
        onClick={handleConfirm}
        disabled={expired || confirming}
      >
        {confirming ? "Confirming..." : "Confirm booking"}
      </button>
    </section>
  );
}

export default PendingBooking;
