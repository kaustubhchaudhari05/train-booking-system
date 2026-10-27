
from datetime import time

from app import create_app
from app.extensions import db
from app.models import Station, Train, TrainRoute


SAMPLE_TRAINS = [
    {
        "train_number": "90001",
        "name": "Nagpur-Bhusaval Demo Express",
        "running_days": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "stops": [
            {
                "station_code": "NGP",
                "stop_order": 1,
                "arrival_time": None,
                "departure_time": time(8, 0),
                "distance_km": 0,
            },
            {
                "station_code": "WR",
                "stop_order": 2,
                "arrival_time": time(9, 15),
                "departure_time": time(9, 20),
                "distance_km": 80,
            },
            {
                "station_code": "BSL",
                "stop_order": 3,
                "arrival_time": time(12, 30),
                "departure_time": None,
                "distance_km": 280,
            },
        ],
    }
]


def seed_trains():
    app = create_app()

    with app.app_context():
        inserted = 0

        for train_data in SAMPLE_TRAINS:
            existing = db.session.execute(
                db.select(Train).where(
                    Train.train_number == train_data["train_number"]
                )
            ).scalar_one_or_none()

            if existing:
                print(f"Already exists: {train_data['train_number']}")
                continue

            train = Train(
                train_number=train_data["train_number"],
                name=train_data["name"],
                running_days=train_data["running_days"],
            )

            for stop in train_data["stops"]:
                station = db.session.execute(
                    db.select(Station).where(
                        Station.code == stop["station_code"]
                    )
                ).scalar_one_or_none()

                if station is None:
                    raise ValueError(
                        f"Station not found: {stop['station_code']}"
                    )

                train.routes.append(
                    TrainRoute(
                        station=station,
                        stop_order=stop["stop_order"],
                        arrival_time=stop["arrival_time"],
                        departure_time=stop["departure_time"],
                        distance_km=stop["distance_km"],
                    )
                )

            db.session.add(train)
            inserted += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        print(f"Train seeding complete. Inserted {inserted} trains.")


if __name__ == "__main__":
    seed_trains()
