import { useEffect, useState } from "react";
import {
  COACH_CLASSES,
  getStations,
  searchTrains,
  type CoachClass,
  type Station,
  type TrainSearchResult,
} from "./api";
import SeatAvailability from "./components/SeatAvailability";
import "./App.css";

interface ClassSelection {
  scheduleId: number;
  coachClass: CoachClass;
}

function App() {
  const [stations, setStations] = useState<Station[]>([]);
  const [source, setSource] = useState("");
  const [destination, setDestination] = useState("");
  const [journeyDate, setJourneyDate] = useState("");
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

  const today = new Date();
  const minDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (source === destination) {
      setError("Source and destination must be different.");
      setTrains([]);
      setSearched(false);
      return;
    }

    setError("");
    setTrains([]);
    setSelection(null);
    setSearching(true);
    setSearched(false);

    try {
      const result = await searchTrains({
        source,
        destination,
        date: journeyDate,
      });

      setTrains(result.trains);
      setSearched(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to search trains.",
      );
    } finally {
      setSearching(false);
    }
  }

  return (
    <main className="page">
      <header className="site-header">
        <div className="brand">
          <span className="brand-icon">🚆</span>
          <span>Railway</span>
        </div>
        <span className="header-label">Train Booking System</span>
      </header>

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

        {searching && (
          <p className="status-message">Searching trains...</p>
        )}

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
                    <div className="train-heading">
                      <div>
                        <h3>{train.name}</h3>
                        <span className="train-number">
                          Train no. {train.train_number}
                        </span>
                      </div>
                      <span className="distance">
                        {train.distance_km} km
                      </span>
                    </div>

                    <div className="journey-times">
                      <div>
                        <strong>{train.source.departure_time ?? "N/A"}</strong>
                        <p>{train.source.name}</p>
                        <span>{train.source.code}</span>
                      </div>

                      <div className="journey-arrow" aria-hidden="true">
                        ───→
                      </div>

                      <div className="destination-time">
                        <strong>{train.destination.arrival_time ?? "N/A"}</strong>
                        <p>{train.destination.name}</p>
                        <span>{train.destination.code}</span>
                      </div>
                    </div>

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
                      <SeatAvailability
                        key={`${train.schedule_id}-${selection.coachClass}`}
                        train={train}
                        coachClass={selection.coachClass}
                      />
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

      </section>

      <footer className="site-footer">
        Built for your next railway journey.
      </footer>
    </main>
  );
}

export default App;
