import { Link, Navigate, useLocation } from "react-router-dom";
import {
  type CoachClass,
  type ConfirmedBooking,
  type TrainSearchResult,
} from "../api";
import TrainSummary from "../components/TrainSummary";
import { formatJourneyDate, passengerSeatLabel } from "../format";

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
      {booking.status === "WAITLISTED" ? (
        <>
          <p className="confirmed-badge waitlist-badge">Waitlisted</p>
          <h1>Your booking is on the waitlist.</h1>
        </>
      ) : (
        <>
          <p className="confirmed-badge">✓ Booking confirmed</p>
          <h1>Your ticket is confirmed.</h1>
        </>
      )}

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

          {booking.passengers.some((p) => p.status === "WAITLISTED") && (
            <p className="booking-notice">
              Waitlisted passengers get a seat automatically, in waitlist
              order, when one becomes free. Check the booking details for
              updates.
            </p>
          )}

          <ul className="booked-passengers">
            {booking.passengers.map((passenger) => (
              <li key={passenger.id}>
                <span>
                  {passenger.passenger_name} ({passenger.age},{" "}
                  {passenger.gender.toLowerCase()})
                </span>
                <strong>{passengerSeatLabel(passenger, booking.status)}</strong>
              </li>
            ))}
          </ul>
        </section>
      </article>

      <div className="page-actions">
        <Link
          className="book-button book-link"
          to={`/booking/${booking.booking_reference}`}
        >
          View booking
        </Link>
        <Link className="link-button" to="/">
          Book another journey
        </Link>
      </div>
    </section>
  );
}

export default ConfirmationPage;
