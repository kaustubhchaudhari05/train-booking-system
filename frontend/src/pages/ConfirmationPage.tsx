import { Link, Navigate, useLocation } from "react-router-dom";
import {
  type CoachClass,
  type ConfirmedBooking,
  type TrainSearchResult,
} from "../api";
import TrainSummary from "../components/TrainSummary";
import { BERTH_LABELS, formatJourneyDate } from "../format";

export interface ConfirmationPageState {
  train: TrainSearchResult;
  coachClass: CoachClass;
  booking: ConfirmedBooking;
}

function ConfirmationPage() {
  const state = useLocation().state as ConfirmationPageState | null;

  // Booking lookup by reference arrives in Phase 6; until then this page
  // only works when reached from a successful confirmation.
  if (!state?.booking || !state.train) {
    return <Navigate to="/" replace />;
  }

  const { train, coachClass, booking } = state;

  return (
    <section className="booking-page">
      <p className="confirmed-badge">✓ Booking confirmed</p>
      <h1>Your ticket is confirmed.</h1>

      <article className="train-card">
        <TrainSummary train={train} />

        <p className="booking-meta booking-trip">
          Class <strong>{coachClass}</strong> · Journey date{" "}
          <strong>{formatJourneyDate(train.journey_date)}</strong>
        </p>

        <section className="booking-result">
          <p className="booking-meta">
            Booking reference <strong>{booking.booking_reference}</strong>
          </p>
          <p className="booking-meta">
            Status <strong>{booking.status}</strong> · Total{" "}
            <strong>₹{booking.total_amount}</strong>
          </p>

          <ul className="booked-passengers">
            {booking.passengers.map((passenger, index) => (
              <li key={index}>
                <span>
                  {passenger.passenger_name} ({passenger.age},{" "}
                  {passenger.gender.toLowerCase()})
                </span>
                <strong>
                  {passenger.coach_number} / {passenger.seat_number}{" "}
                  {BERTH_LABELS[passenger.berth_type] ?? passenger.berth_type}
                </strong>
              </li>
            ))}
          </ul>
        </section>
      </article>

      <Link className="book-button book-link" to="/">
        Book another journey
      </Link>
    </section>
  );
}

export default ConfirmationPage;
