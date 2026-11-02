import { Link } from "react-router-dom";
import { type BookingResult } from "../api";
import { passengerSeatLabel } from "../format";

interface WaitlistedBookingProps {
  booking: BookingResult;
}

// Shown when no seats were free, so the whole booking is waitlisted.
// It needs no confirmation; passengers are promoted automatically.
function WaitlistedBooking({ booking }: WaitlistedBookingProps) {
  return (
    <section className="booking-result" aria-live="polite">
      <h4>Booking waitlisted</h4>

      <p className="booking-notice">
        No seats were free, so all passengers are on the waitlist. Each
        passenger gets a seat automatically, in waitlist order, when one
        becomes free. No confirmation is needed.
      </p>

      <p className="booking-meta">
        Booking reference <strong>{booking.booking_reference}</strong>
      </p>
      <p className="booking-meta">
        Status <strong>{booking.status}</strong> · Total{" "}
        <strong>₹{booking.total_amount}</strong>
      </p>

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

      <Link
        className="book-button book-link"
        to={`/booking/${booking.booking_reference}`}
      >
        View booking
      </Link>
    </section>
  );
}

export default WaitlistedBooking;
