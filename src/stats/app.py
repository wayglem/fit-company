import logging
import sys
import os

from flask import Flask, request, jsonify
from .database import init_db, db_session
from .models_db import WorkoutStat
from .models_dto import WorkoutStatSchema
from pydantic import ValidationError

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URI", "postgresql://postgres:docker@stats-db:5432/stats"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

BOOTSTRAP_KEY = os.environ.get("BOOTSTRAP_KEY", "stats-bootstrap-key")


@app.route("/health")
def health():
    return {"status": "STATS SERVICE UP"}


@app.route("/stats", methods=["GET"])
def get_stats():
    try:
        db = db_session()
        stats = db.query(WorkoutStat).all()
        result = [
            {
                "user_id": stat.user_id,
                "workout_id": stat.workout_id,
                "performed_at": stat.performed_at.isoformat(),
            }
            for stat in stats
        ]
        db.close()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Failed to fetch stats: {e}")
        return jsonify({"error": "Failed to fetch stats"}), 500


@app.route("/bootstrap/fake-stat", methods=["POST"])
def create_fake_stat():
    """
    Optional endpoint to create fake workout stats for testing.
    Requires X-Bootstrap-Key header for authorization.
    """
    try:
        bootstrap_key = request.headers.get("X-Bootstrap-Key")
        if not bootstrap_key or bootstrap_key != BOOTSTRAP_KEY:
            return jsonify({"error": "Invalid bootstrap key"}), 401

        data = request.get_json()
        stat_data = WorkoutStatSchema.model_validate(data)

        db = db_session()
        new_stat = WorkoutStat(
            user_id=stat_data.user_id,
            workout_id=stat_data.workout_id,
            performed_at=stat_data.performed_at
        )
        db.add(new_stat)
        db.commit()
        db.close()

        return (
            jsonify(
                {
                    "message": "Workout stat created",
                    "user_id": stat_data.user_id,
                    "workout_id": stat_data.workout_id,
                }
            ),
            201,
        )
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Error creating stat: {e}")
        return jsonify({"error": "Error creating stat", "details": str(e)}), 500


def run_app():
    init_db()
    app.run(host="0.0.0.0", port=5002, debug=True)


if __name__ == "__main__":
    run_app()
