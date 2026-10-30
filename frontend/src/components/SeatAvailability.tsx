import { useEffect, useState } from "react";
import {
  getSeatAvailability,
  type CoachClass,
  type TrainSearchResult,
} from "../api";

interface SeatAvailabilityProps {
  train: TrainSearchResult;
  coachClass: CoachClass;
}

// Mount with a key of schedule + class so each selection starts fresh.
function SeatAvailability({ train, coachClass }: SeatAvailabilityProps) {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getSeatAvailability({
      scheduleId: train.schedule_id,
      coachClass,
      sourceStopOrder: train.source.stop_order,
      destinationStopOrder: train.destination.stop_order,
    })
      .then((result) => {
        if (!cancelled) {
          setCount(result.count);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load seat availability.",
          );
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
    return <p className="status-message">Checking seat availability...</p>;
  }

  if (error) {
    return <p className="error-message">{error}</p>;
  }

  if (count === 0) {
    return (
      <p className="status-message">
        No seats available
      </p>
    );
  }

  return (
    <p className="availability-count">
      <strong>{count}</strong> seat{count === 1 ? "" : "s"} available
    </p>
  );
}

export default SeatAvailability;
