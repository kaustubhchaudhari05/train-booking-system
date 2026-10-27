from app import create_app
from app.extensions import db
from app.models import Station


SAMPLE_STATIONS = [
    {
        "code": "NGP",
        "name": "Nagpur Junction",
        "city": "Nagpur",
        "state": "Maharashtra",
    },
    {
        "code": "WR",
        "name": "Wardha Junction",
        "city": "Wardha",
        "state": "Maharashtra",
    },
    {
        "code": "BSL",
        "name": "Bhusaval Junction",
        "city": "Bhusaval",
        "state": "Maharashtra",
    },
    {
        "code": "PUNE",
        "name": "Pune Junction",
        "city": "Pune",
        "state": "Maharashtra",
    },
    {
        "code": "MMR",
        "name": "Manmad Junction",
        "city": "Manmad",
        "state": "Maharashtra",
    },
]


def seed_stations():
    app = create_app()

    with app.app_context():
        inserted = 0

        for station_data in SAMPLE_STATIONS:
            existing_station = db.session.execute(
                db.select(Station).where(
                    Station.code == station_data["code"]
                )
            ).scalar_one_or_none()

            if existing_station:
                print(f"Already exists: {station_data['code']}")
                continue

            db.session.add(Station(**station_data))
            inserted += 1

        db.session.commit()
        print(f"Station seeding complete. Inserted {inserted} stations.")


if __name__ == "__main__":
    seed_stations()
