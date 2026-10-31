import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { type CoachClass, type TrainSearchResult } from "../api";
import BookingForm from "../components/BookingForm";
import TrainSummary from "../components/TrainSummary";
import { formatJourneyDate } from "../format";

export interface BookingPageState {
  train: TrainSearchResult;
  coachClass: CoachClass;
}

function BookingPage() {
  const navigate = useNavigate();
  const state = useLocation().state as BookingPageState | null;

  // The selected train only arrives through navigation state, so a
  // direct visit to /book goes back to search.
  if (!state?.train || !state.coachClass) {
    return <Navigate to="/" replace />;
  }

  const { train, coachClass } = state;

  return (
    <section className="booking-page">
      <button
        type="button"
        className="link-button"
        onClick={() => navigate(-1)}
      >
        ← Back to results
      </button>

      <h1>Book your tickets</h1>

      <article className="train-card">
        <TrainSummary train={train} />

        <p className="booking-meta booking-trip">
          Class <strong>{coachClass}</strong> · Journey date{" "}
          <strong>{formatJourneyDate(train.journey_date)}</strong>
        </p>

        <BookingForm train={train} coachClass={coachClass} />
      </article>
    </section>
  );
}

export default BookingPage;
