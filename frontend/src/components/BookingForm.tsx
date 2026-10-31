import { useEffect, useState } from "react";
import {
  createBooking,
  getFareQuote,
  MAX_PASSENGERS,
  type BerthPreference,
  type BookingResult,
  type CoachClass,
  type Gender,
  type TrainSearchResult,
} from "../api";
import PendingBooking from "./PendingBooking";

const BERTH_OPTIONS: { value: BerthPreference; label: string }[] = [
  { value: "NO_PREFERENCE", label: "No preference" },
  { value: "LOWER", label: "Lower" },
  { value: "MIDDLE", label: "Middle" },
  { value: "UPPER", label: "Upper" },
  { value: "SIDE_LOWER", label: "Side lower" },
  { value: "SIDE_UPPER", label: "Side upper" },
];

// Age is kept as text so the input can be empty while typing.
interface PassengerFormRow {
  name: string;
  age: string;
  gender: Gender | "";
  berthPreference: BerthPreference;
}

const emptyPassenger = (): PassengerFormRow => ({
  name: "",
  age: "",
  gender: "",
  berthPreference: "NO_PREFERENCE",
});

interface BookingFormProps {
  train: TrainSearchResult;
  coachClass: CoachClass;
}

function BookingForm({ train, coachClass }: BookingFormProps) {
  const [passengers, setPassengers] = useState<PassengerFormRow[]>([
    emptyPassenger(),
  ]);
  const [totalFare, setTotalFare] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [booking, setBooking] = useState<BookingResult | null>(null);

  const passengerCount = passengers.length;

  useEffect(() => {
    let cancelled = false;

    getFareQuote({
      scheduleId: train.schedule_id,
      sourceStationId: train.source.station_id,
      destinationStationId: train.destination.station_id,
      coachClass,
      passengers: passengerCount,
    })
      .then((quote) => {
        if (!cancelled) {
          setTotalFare(quote.total_fare);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTotalFare(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [train, coachClass, passengerCount]);

  function updatePassenger(
    index: number,
    changes: Partial<PassengerFormRow>,
  ) {
    setPassengers((current) =>
      current.map((passenger, i) =>
        i === index ? { ...passenger, ...changes } : passenger,
      ),
    );
  }

  function addPassenger() {
    setPassengers((current) =>
      current.length < MAX_PASSENGERS
        ? [...current, emptyPassenger()]
        : current,
    );
  }

  function removePassenger(index: number) {
    setPassengers((current) => current.filter((_, i) => i !== index));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    for (const [index, passenger] of passengers.entries()) {
      const age = Number(passenger.age);

      if (!passenger.name.trim()) {
        setError(`Enter a name for passenger ${index + 1}.`);
        return;
      }

      if (passenger.age === "" || !Number.isInteger(age) || age < 0 || age > 120) {
        setError(`Enter an age between 0 and 120 for passenger ${index + 1}.`);
        return;
      }

      if (!passenger.gender) {
        setError(`Select a gender for passenger ${index + 1}.`);
        return;
      }
    }

    setSubmitting(true);

    try {
      const result = await createBooking({
        train,
        coachClass,
        passengers: passengers.map((passenger) => ({
          passenger_name: passenger.name.trim(),
          age: Number(passenger.age),
          gender: passenger.gender as Gender,
          berth_preference: passenger.berthPreference,
        })),
      });

      setBooking(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to create booking.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (booking) {
    return (
      <PendingBooking booking={booking} train={train} coachClass={coachClass} />
    );
  }

  return (
    <form className="booking-form" onSubmit={handleSubmit} noValidate>
      <h4>Passenger details</h4>

      {passengers.map((passenger, index) => (
        <fieldset className="passenger-row" key={index}>
          <legend>Passenger {index + 1}</legend>

          <div className="form-field">
            <label htmlFor={`name-${index}`}>Name</label>
            <input
              id={`name-${index}`}
              value={passenger.name}
              maxLength={100}
              onChange={(event) =>
                updatePassenger(index, { name: event.target.value })
              }
            />
          </div>

          <div className="form-field">
            <label htmlFor={`age-${index}`}>Age</label>
            <input
              id={`age-${index}`}
              type="number"
              min={0}
              max={120}
              value={passenger.age}
              onChange={(event) =>
                updatePassenger(index, { age: event.target.value })
              }
            />
          </div>

          <div className="form-field">
            <label htmlFor={`gender-${index}`}>Gender</label>
            <select
              id={`gender-${index}`}
              value={passenger.gender}
              onChange={(event) =>
                updatePassenger(index, {
                  gender: event.target.value as Gender | "",
                })
              }
            >
              <option value="">Select</option>
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div className="form-field">
            <label htmlFor={`berth-${index}`}>Berth preference</label>
            <select
              id={`berth-${index}`}
              value={passenger.berthPreference}
              onChange={(event) =>
                updatePassenger(index, {
                  berthPreference: event.target.value as BerthPreference,
                })
              }
            >
              {BERTH_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {passengers.length > 1 && (
            <button
              type="button"
              className="link-button"
              onClick={() => removePassenger(index)}
            >
              Remove
            </button>
          )}
        </fieldset>
      ))}

      {passengers.length < MAX_PASSENGERS && (
        <button type="button" className="link-button" onClick={addPassenger}>
          + Add passenger
        </button>
      )}

      <p className="fare-summary">
        Total fare for {passengerCount} passenger
        {passengerCount === 1 ? "" : "s"}:{" "}
        <strong>{totalFare ? `₹${totalFare}` : "—"}</strong>
      </p>

      {error && <p className="error-message">{error}</p>}

      <button className="search-button" type="submit" disabled={submitting}>
        {submitting ? "Booking..." : "Book seats"}
      </button>
    </form>
  );
}

export default BookingForm;
