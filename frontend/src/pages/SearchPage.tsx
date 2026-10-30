import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  COACH_CLASSES,
  getStations,
  searchTrains,
  type CoachClass,
  type Station,
  type TrainSearchResult,
} from "../api";
import FareSummary from "../components/FareSummary";
import SeatAvailability from "../components/SeatAvailability";
import TrainSummary from "../components/TrainSummary";
import { type BookingPageState } from "./BookingPage";

interface ClassSelection {
  scheduleId: number;
  coachClass: CoachClass;
}

function SearchPage() {
  const navigate = useNavigate();
  // The submitted search lives in the URL so that browser back from the
  // booking page, or a refresh, restores the same results.
  const [searchParams, setSearchParams] = useSearchParams();
  const querySource = searchParams.get("source") ?? "";
  const queryDestination = searchParams.get("destination") ?? "";
  const queryDate = searchParams.get("date") ?? "";

  const [stations, setStations] = useState<Station[]>([]);
  const [source, setSource] = useState(querySource);
  const [destination, setDestination] = useState(queryDestination);
  const [journeyDate, setJourneyDate] = useState(queryDate);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [trains, setTrains] = useState<TrainSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selection, setSelection] = useState<ClassSelection | null>(null);

  useEffect(() => {
    async function loadStations() {
      try {
        setError("");
        const data = await getStations();
        setStations(data);
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Something went wrong.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadStations();
  }, []);

  useEffect(() => {
    if (!querySource || !queryDestination || !queryDate) {
      return;
    }

    let cancelled = false;

    setError("");
    setTrains([]);
    setSelection(null);
    setSearching(true);
    setSearched(false);

    searchTrains({
      source: querySource,
      destination: queryDestination,
      date: queryDate,
    })
      .then((result) => {
        if (!cancelled) {
          setTrains(result.trains);
          setSearched(true);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to search trains.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setSearching(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [querySource, queryDestination, queryDate]);

  const today = new Date();
  const minDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (source === destination) {
      setError("Source and destination must be different.");
      setTrains([]);
      setSearched(false);
      return;
    }

    setSearchParams({ source, destination, date: journeyDate });
  }

  function openBooking(train: TrainSearchResult, coachClass: CoachClass) {
    const state: BookingPageState = { train, coachClass };
    navigate("/book", { state });
  }

  return (
    <section className="hero">
      <p className="eyebrow">YOUR JOURNEY STARTS HERE</p>
      <h1>Find your next journey.</h1>
      <p className="hero-description">
        Search trains, explore routes, and plan your next trip.
      </p>

      <form className="search-card" onSubmit={handleSearch}>
        <div className="form-field">
          <label htmlFor="source">From</label>
          <select
            id="source"
            value={source}
            onChange={(event) => setSource(event.target.value)}
            required
            disabled={loading || stations.length === 0}
          >
            <option value="">Select departure station</option>
            {stations.map((station) => (
              <option key={station.id} value={station.code}>
                {station.name} ({station.code})
              </option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="destination">To</label>
          <select
            id="destination"
            value={destination}
            onChange={(event) => setDestination(event.target.value)}
            required
            disabled={loading || stations.length === 0}
          >
            <option value="">Select destination station</option>
            {stations.map((station) => (
              <option key={station.id} value={station.code}>
                {station.name} ({station.code})
              </option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="journeyDate">Journey date</label>
          <input
            id="journeyDate"
            type="date"
            min={minDate}
            value={journeyDate}
            onChange={(event) => setJourneyDate(event.target.value)}
            required
          />
        </div>

        {loading && <p className="status-message">Loading stations...</p>}

        {error && <p className="error-message">{error}</p>}

        <button
          className="search-button"
          type="submit"
          disabled={loading || stations.length === 0}
        >
          Search trains <span aria-hidden="true">→</span>
        </button>
      </form>

      {searching && <p className="status-message">Searching trains...</p>}

      {searched && !searching && (
        <section className="results-section">
          <h2>Available trains</h2>
          <p className="results-count">
            {trains.length} train{trains.length === 1 ? "" : "s"} found
          </p>

          {trains.length === 0 ? (
            <p>No trains found for this route and date.</p>
          ) : (
            <div className="train-list">
              {trains.map((train) => (
                <article className="train-card" key={train.schedule_id}>
                  <TrainSummary train={train} />

                  <div
                    className="class-picker"
                    role="group"
                    aria-label={`Select class for ${train.name}`}
                  >
                    {COACH_CLASSES.map((coachClass) => {
                      const isSelected =
                        selection?.scheduleId === train.schedule_id &&
                        selection.coachClass === coachClass;

                      return (
                        <button
                          key={coachClass}
                          type="button"
                          className="class-button"
                          aria-pressed={isSelected}
                          onClick={() =>
                            setSelection(
                              isSelected
                                ? null
                                : {
                                    scheduleId: train.schedule_id,
                                    coachClass,
                                  },
                            )
                          }
                        >
                          {coachClass}
                        </button>
                      );
                    })}
                  </div>

                  {selection?.scheduleId === train.schedule_id && (
                    <>
                      <SeatAvailability
                        key={`seats-${train.schedule_id}-${selection.coachClass}`}
                        train={train}
                        coachClass={selection.coachClass}
                      />
                      <FareSummary
                        key={`fare-${train.schedule_id}-${selection.coachClass}`}
                        train={train}
                        coachClass={selection.coachClass}
                      />
                      <button
                        type="button"
                        className="book-button"
                        onClick={() =>
                          openBooking(train, selection.coachClass)
                        }
                      >
                        Book now
                      </button>
                    </>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </section>
  );
}

export default SearchPage;
