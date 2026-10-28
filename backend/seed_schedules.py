from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Train, TrainSchedule


def seed_schedules():
    app = create_app()

    with app.app_context():
        train = db.session.execute(
            db.select(Train).where(
                Train.train_number == "90001"
            )
        ).scalar_one_or_none()

        if train is None:
            raise ValueError(
                "Train 90001 not found. Run seed_trains.py first."
            )

        inserted = 0

        # Create schedules for the next 7 days.
        today = date.today()

        for offset in range(7):
            journey_date = today + timedelta(days=offset)

            existing = db.session.execute(
                db.select(TrainSchedule).where(
                    TrainSchedule.train_id == train.id,
                    TrainSchedule.journey_date == journey_date,
                )
            ).scalar_one_or_none()

            if existing:
                print(f"Already exists: {journey_date}")
                continue

            db.session.add(
                TrainSchedule(
                    train_id=train.id,
                    journey_date=journey_date,
                    status="SCHEDULED",
                )
            )
            inserted += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        print(f"Schedule seeding complete. Inserted {inserted} schedules.")


if __name__ == "__main__":
    seed_schedules()
