export const BERTH_LABELS: Record<string, string> = {
  LOWER: "Lower",
  MIDDLE: "Middle",
  UPPER: "Upper",
  SIDE_LOWER: "Side lower",
  SIDE_UPPER: "Side upper",
  SEAT: "Seat",
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
