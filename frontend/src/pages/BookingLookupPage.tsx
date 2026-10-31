import { useState } from "react";
import { useNavigate } from "react-router-dom";

function BookingLookupPage() {
  const navigate = useNavigate();
  const [reference, setReference] = useState("");
  const [error, setError] = useState("");

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
      <h1>Find your booking</h1>

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

export default BookingLookupPage;
