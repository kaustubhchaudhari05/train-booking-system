from app import create_app
from app.extensions import db
from app.models import Train, Coach, Seat

app = create_app()

# Demo coach configuration: class, coach number, capacity
COACH_CONFIG = [
    ("SL", "S1", 24),
("3A", "B1", 18),
    ("2A", "A1", 12),
    ("1A", "H1", 6),
]

# Simplified demo berth layouts, not real railway layouts
BERTH_LAYOUTS = {
    "SL": ["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER"],
    "3A": ["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER"],
    "2A": ["LOWER", "UPPER", "SIDE_LOWER", "SIDE_UPPER"],
    "1A": ["LOWER", "UPPER"],
}


def berth_type_for(coach_class, seat_number):
    layout = BERTH_LAYOUTS[coach_class]
    return layout[(seat_number - 1) % len(layout)]


with app.app_context():
    train = Train.query.filter_by(train_number="90001").first()

    if not train:
        raise SystemExit(
            "Demo train 90001 not found. Seed trains first."
        )

    for coach_class, coach_number, capacity in COACH_CONFIG:
        coach = Coach.query.filter_by(
            train_id=train.id,
            coach_number=coach_number,
        ).first()

        if coach is None:
            coach = Coach(
                train_id=train.id,
                coach_number=coach_number,
                coach_class=coach_class,
            )
            db.session.add(coach)
            db.session.flush()
        elif coach.coach_class != coach_class:
            raise ValueError(
                f"Coach {coach_number} already exists with a "
                "different class. Resolve it before reseeding."
            )

        for number in range(1, capacity + 1):
            seat_number = str(number)

            seat = Seat.query.filter_by(
                coach_id=coach.id,
                seat_number=seat_number,
            ).first()

            if seat is None:
                db.session.add(
                    Seat(
                        coach_id=coach.id,
                        seat_number=seat_number,
                        berth_type=berth_type_for(
                            coach_class, number
                        ),
                    )
                )

    db.session.commit()

    print("Coach and seat seeding completed.")
    for coach_class, coach_number, capacity in COACH_CONFIG:
        print(
            f"{coach_number} ({coach_class}): "
            f"{capacity} seats/berths"
        )
