from flask import Flask, jsonify

from config import Config
from app.extensions import db, migrate
from app.routes.stations import stations_bp
from app.routes.trains import trains_bp
from app.routes.booking import booking_bp
from app import models
from app.routes.availability import availability_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(stations_bp)
    app.register_blueprint(trains_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(booking_bp)
    @app.get("/api/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "train-booking-api",
            "message": "Train Booking API is running",
        }), 200

    @app.get("/api/health/db")
    def database_health_check():
        from sqlalchemy import text

        try:
            with db.engine.connect() as connection:
                database_name = connection.execute(
                    text("SELECT current_database()")
                ).scalar_one()

            return jsonify({
                "status": "healthy",
                "database": database_name,
                "message": "PostgreSQL connection successful",
            }), 200

        except Exception:
            app.logger.exception("Database health check failed")
            return jsonify({
                "status": "error",
                "message": "Database connection failed",
            }), 503

    return app
