import { type BookedPassenger } from "./api";

export const BERTH_LABELS: Record<string, string> = {
  LOWER: "Lower",
  MIDDLE: "Middle",
  UPPER: "Upper",
  SIDE_LOWER: "Side lower",
  SIDE_UPPER: "Side upper",
  SEAT: "Seat",
};

// Booking status -> status-pill colour class.
export const STATUS_CLASS: Record<string, string> = {
  CONFIRMED: "status-confirmed",
  PENDING: "status-pending",
  WAITLISTED: "status-pending",
  CANCELLED: "status-closed",
  EXPIRED: "status-closed",
};

export function formatJourneyDate(isoDate: string) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString([], {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatTime(isoString: string | null) {
  if (!isoString) {
    return "N/A";
  }

  return new Date(isoString).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// What to show in a passenger's seat column: the seat once confirmed,
// otherwise the waitlist position or the passenger's state.
export function passengerSeatLabel(
  passenger: BookedPassenger,
  bookingStatus = "PENDING",
) {
  if (passenger.status === "CANCELLED") {
    return "Cancelled";
  }

  if (passenger.seat_number) {
    const berth = passenger.berth_type ?? "";
    return `${passenger.coach_number} / ${passenger.seat_number} ${
      BERTH_LABELS[berth] ?? berth
    }`;
  }

  const bookingLive = ["PENDING", "CONFIRMED", "WAITLISTED"].includes(
    bookingStatus,
  );

  if (passenger.status === "WAITLISTED" && bookingLive) {
    return passenger.waitlist_position
      ? `WL ${passenger.waitlist_position}`
      : "Waitlisted";
  }

  // A seated passenger without seat details is still awaiting
  // confirmation; for expired bookings there is nothing to show.
  return bookingStatus === "PENDING" ? "Pending" : "—";
}
