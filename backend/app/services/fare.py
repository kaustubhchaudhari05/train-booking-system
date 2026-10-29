from decimal import Decimal, ROUND_HALF_UP

from app.models.fare import Fare
from app.models.train_route import TrainRoute


def calculate_fare(
    train_id: int,
    source_station_id: int,
    destination_station_id: int,
    coach_class: str,
) -> Decimal:
    if coach_class not in {"SL", "3A", "2A", "1A"}:
        raise ValueError("Invalid coach class.")

    source = TrainRoute.query.filter_by(
        train_id=train_id,
        station_id=source_station_id,
    ).first()

    destination = TrainRoute.query.filter_by(
        train_id=train_id,
        station_id=destination_station_id,
    ).first()

    if source is None or destination is None:
        raise ValueError(
            "Source or destination station is not on this train's route."
        )

    if source.stop_order >= destination.stop_order:
        raise ValueError(
            "Destination station must come after source station."
        )

    distance_km = (
        Decimal(str(destination.distance_km))
        - Decimal(str(source.distance_km))
    )

    if distance_km <= 0:
        raise ValueError("Journey distance must be positive.")

    fare_config = Fare.query.filter_by(
        coach_class=coach_class
    ).first()

    if fare_config is None:
        raise ValueError(
            f"Fare configuration not found for {coach_class}."
        )

    calculated_fare = max(
        distance_km * Decimal(str(fare_config.fare_per_km)),
        Decimal(str(fare_config.minimum_fare)),
    )

    return calculated_fare.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
