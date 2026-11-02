import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createPaymentOrder,
  verifyPayment,
  type BookingResult,
  type CoachClass,
  type RazorpayCheckoutResult,
  type TrainSearchResult,
} from "../api";
import { formatTime, passengerSeatLabel } from "../format";
import { openRazorpayCheckout } from "../razorpay";
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
  // "paying" covers the Checkout window; "verifying" the server check.
  const [paying, setPaying] = useState(false);
  const [verifying, setVerifying] = useState(false);
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
  const waitlistedCount = booking.passengers.filter(
    (passenger) => passenger.status === "WAITLISTED",
  ).length;

  const fullyWaitlisted =
    booking.passengers.length > 0 && waitlistedCount === booking.passengers.length;

  async function finishPayment(result: RazorpayCheckoutResult) {
    setVerifying(true);

    try {
      const confirmed = await verifyPayment(result);
      const state: ConfirmationPageState = {
        train,
        coachClass,
        booking: confirmed,
      };

      // Replace /book so browser back does not return to a stale form.
      navigate("/booking/confirmed", { state, replace: true });
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to verify payment.",
      );
      setVerifying(false);
      setPaying(false);
    }
  }

  async function handlePay() {
    setError("");
    setPaying(true);

    try {
      const order = await createPaymentOrder(booking.booking_id);

      await openRazorpayCheckout(
        {
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          order_id: order.order_id,
          name: "Train Booking System",
          description: `Booking ${order.booking_reference}`,
          timeout: order.hold_seconds_left,
          handler: (result) => void finishPayment(result),
          modal: { ondismiss: () => setPaying(false) },
          theme: { color: "#285bd4" },
        },
        // Checkout stays open so the user can retry another method.
        (failure) =>
          setError(failure.error.description ?? "Payment failed. Try again."),
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to start payment.",
      );
      setPaying(false);
    }
  }

  return (
    <section className="booking-result" aria-live="polite">
      <h4>Booking pending payment</h4>

      {expired ? (
        <p className="booking-notice booking-notice-expired">
          The seat hold has expired. Go back to the results and book again.
        </p>
      ) : (
        <p className="booking-notice">
          Your booking is not confirmed yet. Seat numbers are shown after
          payment. Pay before{" "}
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

      {waitlistedCount > 0 && !expired && (
        <p className="booking-notice">
          {fullyWaitlisted
            ? "No seats were free, so all passengers are waitlisted."
            : `Not enough seats were free, so ${waitlistedCount} passenger${
                waitlistedCount === 1 ? " is" : "s are"
              } waitlisted.`}{" "}
          The full total is paid now. Waitlisted passengers join the waitlist
          once payment succeeds and get a seat automatically when one becomes
          free.
        </p>
      )}

      <ul className="booked-passengers">
        {booking.passengers.map((passenger) => (
          <li key={passenger.id}>
            <span>
              {passenger.passenger_name} ({passenger.age},{" "}
              {passenger.gender.toLowerCase()})
            </span>
            <strong>{passengerSeatLabel(passenger)}</strong>
          </li>
        ))}
      </ul>

      {error && <p className="error-message">{error}</p>}

      <button
        className="search-button"
        type="button"
        onClick={handlePay}
        disabled={expired || paying}
      >
        {verifying
          ? "Verifying payment..."
          : paying
            ? "Waiting for payment..."
            : `Pay ₹${booking.total_amount}`}
      </button>
    </section>
  );
}

export default PendingBooking;
