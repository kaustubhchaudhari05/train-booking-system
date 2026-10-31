import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { cancelPassenger, type BookingDetails } from "../api";

interface CancelResult {
  passengerName: string;
  booking: BookingDetails;
}

function CancelTicketPage() {
  const [searchParams] = useSearchParams();
  const [reference, setReference] = useState(
    searchParams.get("reference") ?? "",
  );
  const [passengerName, setPassengerName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<CancelResult | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    const trimmedReference = reference.trim().toUpperCase();
    const trimmedName = passengerName.trim();

    if (!trimmedReference) {
      setError("Enter your booking reference.");
      return;
    }

    if (!trimmedName) {
      setError("Enter the passenger's name exactly as booked.");
      return;
    }

    if (
      !window.confirm(
        `Cancel the ticket for ${trimmedName}? This cannot be undone.`,
      )
    ) {
      return;
    }

    setSubmitting(true);

    try {
      const booking = await cancelPassenger(trimmedReference, trimmedName);
      setResult({ passengerName: trimmedName, booking });
      setPassengerName("");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to cancel the ticket.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="booking-page">
      <h1>Cancel ticket</h1>
      <p className="hero-description cancel-help">
        Enter the booking reference and the passenger's name exactly as it
        was entered when booking. The name is case-sensitive.
      </p>

      <form className="search-card lookup-card" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="cancel-reference">Booking reference</label>
          <input
            id="cancel-reference"
            value={reference}
            maxLength={20}
            onChange={(event) => setReference(event.target.value)}
          />
        </div>

        <div className="form-field">
          <label htmlFor="cancel-name">Passenger name</label>
          <input
            id="cancel-name"
            value={passengerName}
            maxLength={100}
            onChange={(event) => setPassengerName(event.target.value)}
          />
        </div>

        {error && <p className="error-message">{error}</p>}

        <button className="search-button" type="submit" disabled={submitting}>
          {submitting ? "Cancelling..." : "Cancel ticket"}
        </button>
      </form>

      {result && (
        <section className="booking-result" aria-live="polite">
          <p className="booking-notice">
            {result.booking.status === "CANCELLED"
              ? `The ticket for ${result.passengerName} has been cancelled. ` +
                "No passengers are left, so the whole booking is cancelled."
              : `The ticket for ${result.passengerName} has been cancelled. ` +
                `New total: ₹${result.booking.total_amount}.`}
          </p>
          <Link
            className="link-button"
            to={`/booking/${result.booking.booking_reference}`}
          >
            View booking
          </Link>
        </section>
      )}
    </section>
  );
}

export default CancelTicketPage;
