import { useEffect, useState } from "react";
import {
  getFareQuote,
  type CoachClass,
  type FareQuote,
  type TrainSearchResult,
} from "../api";

interface FareSummaryProps {
  train: TrainSearchResult;
  coachClass: CoachClass;
}

// Mount with a key of schedule + class so each selection starts fresh.
function FareSummary({ train, coachClass }: FareSummaryProps) {
  const [quote, setQuote] = useState<FareQuote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getFareQuote({
      scheduleId: train.schedule_id,
      sourceStationId: train.source.station_id,
      destinationStationId: train.destination.station_id,
      coachClass,
    })
      .then((result) => {
        if (!cancelled) {
          setQuote(result);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load fare.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [train, coachClass]);

  if (loading) {
    return <p className="status-message">Loading fare...</p>;
  }

  if (error || !quote) {
    return <p className="error-message">{error || "Fare unavailable."}</p>;
  }

  return (
    <p className="fare-summary">
      Fare: <strong>₹{quote.fare_per_passenger}</strong>
    </p>
  );
}

export default FareSummary;
