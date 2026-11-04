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
    <section className="search-stage">
      <span className="stage-word stage-word-top" aria-hidden="true">
        TRAIN
      </span>
      <span className="stage-word stage-word-bottom" aria-hidden="true">
        BOOK
      </span>

      <div className="search-layout">
        <aside className="filter-panel">
          <h2 className="filter-title">Find trains</h2>

          <form className="filter-form" onSubmit={handleSearch}>
            <div className="form-field">
              <label htmlFor="source">From station</label>
              <select
                id="source"
                value={source}
                onChange={(event) => setSource(event.target.value)}
                required
                disabled={loading || stations.length === 0}
              >
                <option value="">Select one</option>
                {stations.map((station) => (
                  <option key={station.id} value={station.code}>
                    {station.name} ({station.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="destination">To station</label>
              <select
                id="destination"
                value={destination}
                onChange={(event) => setDestination(event.target.value)}
                required
                disabled={loading || stations.length === 0}
              >
                <option value="">Select one</option>
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
              Search trains
            </button>
          </form>
        </aside>

        <div className="results-panel">
          {searched && !searching ? (
            <>
              <h1>Available trains</h1>
              <p className="results-count">
                {trains.length} train{trains.length === 1 ? "" : "s"} found.
                Select a class to see seats and fare.
              </p>
            </>
          ) : (
            <>
              <h1>Find your next journey.</h1>
              <p className="results-count">
                Choose your stations and journey date to see available trains.
              </p>
            </>
          )}

          {searching && (
            <div className="spinner" role="status" aria-label="Searching trains" />
          )}

          {searched && !searching && trains.length === 0 && (
            <p className="empty-results">
              No trains found for this route and date.
            </p>
          )}

          {searched && !searching && trains.length > 0 && (
            <div className="train-list">
              {trains.map((train) => {
                const selectedClass =
                  selection?.scheduleId === train.schedule_id
                    ? selection.coachClass
                    : null;

                return (
                  <article className="ticket-card" key={train.schedule_id}>
                    <div className="ticket-body">
                      <TrainSummary train={train} />

                      <div
                        className="class-picker"
                        role="group"
                        aria-label={`Select class for ${train.name}`}
                      >
                        {COACH_CLASSES.map((coachClass) => {
                          const isSelected = selectedClass === coachClass;

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
                    </div>

                    {selectedClass ? (
                      <div className="ticket-footer">
                        <div className="ticket-footer-info">
                          <SeatAvailability
                            key={`seats-${train.schedule_id}-${selectedClass}`}
                            train={train}
                            coachClass={selectedClass}
                          />
                          <FareSummary
                            key={`fare-${train.schedule_id}-${selectedClass}`}
                            train={train}
                            coachClass={selectedClass}
                          />
                        </div>
                        <button
                          type="button"
                          className="ticket-book-button"
                          onClick={() => openBooking(train, selectedClass)}
                        >
                          Book now
                        </button>
                      </div>
                    ) : (
                      <p className="ticket-footer ticket-footer-idle">
                        Select a class to see seats and fare
                      </p>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="photo-panel" aria-hidden="true">
          <p>Every journey starts at the platform.</p>
        </div>
      </div>
    </section>
  );
}

export default SearchPage;
