import { type TrainSearchResult } from "../api";

interface TrainSummaryProps {
  train: TrainSearchResult;
}

function TrainSummary({ train }: TrainSummaryProps) {
  return (
    <>
      <div className="train-heading">
        <div>
          <h3>{train.name}</h3>
          <span className="train-number">Train no. {train.train_number}</span>
        </div>
        <span className="distance">{train.distance_km} km</span>
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
    </>
  );
}

export default TrainSummary;
