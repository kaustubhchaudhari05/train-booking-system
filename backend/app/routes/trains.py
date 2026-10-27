from flask import Blueprint, jsonify, request
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import Train, TrainRoute, Station

trains_bp = Blueprint("trains", __name__, url_prefix="/api/trains")


@trains_bp.get("/search")
def search_trains():
    source_code = request.args.get("source", "").strip().upper()
    destination_code = request.args.get("destination", "").strip().upper()

    if not source_code or not destination_code:
        return jsonify({
            "error": "Both source and destination are required."
        }), 400

    if source_code == destination_code:
        return jsonify({
            "error": "Source and destination must be different."
        }), 400

    source_route = aliased(TrainRoute)
    destination_route = aliased(TrainRoute)
    source_station = aliased(Station)
    destination_station = aliased(Station)

    statement = (
        db.select(
            Train,
            source_station,
            destination_station,
            source_route,
            destination_route,
        )
        .join(source_route, source_route.train_id == Train.id)
        .join(
            source_station,
            source_station.id == source_route.station_id,
        )
        .join(destination_route, destination_route.train_id == Train.id)
        .join(
            destination_station,
            destination_station.id == destination_route.station_id,
        )
        .where(
            Train.is_active.is_(True),
            source_station.code == source_code,
            destination_station.code == destination_code,
            source_station.is_active.is_(True),
            destination_station.is_active.is_(True),
            source_route.stop_order < destination_route.stop_order,
        )
        .order_by(source_route.departure_time)
    )

    results = db.session.execute(statement).all()

    trains = [
        {
            "train_number": train.train_number,
            "name": train.name,
            "running_days": train.running_days,
            "source": {
                "code": src_station.code,
                "name": src_station.name,
                "departure_time": (
                    src_route.departure_time.strftime("%H:%M")
                    if src_route.departure_time else None
                ),
            },
            "destination": {
                "code": dest_station.code,
                "name": dest_station.name,
                "arrival_time": (
                    dest_route.arrival_time.strftime("%H:%M")
                    if dest_route.arrival_time else None
                ),
            },
            "distance_km": str(
                dest_route.distance_km - src_route.distance_km
            ),
        }
        for (
            train,
            src_station,
            dest_station,
            src_route,
            dest_route,
        ) in results
    ]

    return jsonify({
        "count": len(trains),
        "trains": trains,
    }), 200
