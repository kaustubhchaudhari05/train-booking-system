from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Station

stations_bp = Blueprint("stations", __name__, url_prefix="/api/stations")


@stations_bp.get("")
def list_stations():
    stations = db.session.execute(
        db.select(Station)
        .where(Station.is_active.is_(True))
        .order_by(Station.name)
    ).scalars().all()

    return jsonify({
        "count": len(stations),
        "stations": [
            {
                "id": station.id,
                "code": station.code,
                "name": station.name,
                "city": station.city,
                "state": station.state,
            }
            for station in stations
        ],
    }), 200


@stations_bp.get("/<string:code>")
def get_station(code):
    station = db.session.execute(
        db.select(Station).where(
            db.func.upper(Station.code) == code.upper(),
            Station.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if station is None:
        return jsonify({
            "error": "Station not found",
            "code": code,
        }), 404

    return jsonify({
        "id": station.id,
        "code": station.code,
        "name": station.name,
        "city": station.city,
        "state": station.state,
    }), 200
