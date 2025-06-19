import logging
import sys
import os

from flask import Flask, request, jsonify
from .database import init_db, db_session
from .models_db import Subscription
from .models_dto import SubscriptionSchema
from .rabbitmq_service import event_publisher
from pydantic import ValidationError
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URI", "postgresql://postgres:docker@billing-db:5432/billing-db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

BOOTSTRAP_KEY = os.environ.get("BOOTSTRAP_KEY", "billing-bootstrap-key")


@app.route("/health")
def health():
    return {"status": "BILLING SERVICE UP"}


@app.route("/subscribe", methods=["POST"])
def subscribe():
    try:
        data = request.get_json()
        sub_data = SubscriptionSchema.model_validate(data)

        db = db_session()
        subscription = db.query(Subscription).filter_by(user_email=sub_data.user_email).first()

        if subscription:
            subscription.status = "active"
            subscription.subscription_date = datetime.utcnow()
            subscription.expiry_date = datetime.utcnow() + timedelta(days=30)
        else:
            subscription = Subscription(
                user_email=sub_data.user_email,
                status="active",
                subscription_date=datetime.utcnow(),
                expiry_date=datetime.utcnow() + timedelta(days=30),
            )
            db.add(subscription)

        db.commit()
        expiry_date_iso = subscription.expiry_date.isoformat()
        db.close()

        event_publisher.publish_event("SubscriptionActivated", {
            "user_email": sub_data.user_email,
            "expiry_date": expiry_date_iso,
        })

        return jsonify({"message": "Subscription successful", "user_email": sub_data.user_email}), 201
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Subscription error: {e}")
        return jsonify({"error": "Error during subscription"}), 500


@app.route("/cancel", methods=["POST"])
def cancel_subscription():
    try:
        data = request.get_json()
        sub_data = SubscriptionSchema.model_validate(data)

        db = db_session()
        subscription = db.query(Subscription).filter_by(user_email=sub_data.user_email).first()

        if not subscription:
            return jsonify({"error": "Subscription not found"}), 404

        subscription.status = "canceled"
        db.commit()
        db.close()

        event_publisher.publish_event("SubscriptionCanceled", {
            "user_email": sub_data.user_email,
        })

        return jsonify({"message": "Subscription canceled", "user_email": sub_data.user_email}), 200
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Cancel error: {e}")
        return jsonify({"error": "Error during cancelation"}), 500


@app.route("/bootstrap/fake-subscription", methods=["POST"])
def create_fake_subscription():
    """
    Bootstrap endpoint to create a fake subscription for testing.
    Requires X-Bootstrap-Key for auth.
    """
    try:
        bootstrap_key = request.headers.get("X-Bootstrap-Key")
        if not bootstrap_key or bootstrap_key != BOOTSTRAP_KEY:
            return jsonify({"error": "Invalid bootstrap key"}), 401

        data = request.get_json()
        sub_data = SubscriptionSchema.model_validate(data)

        db = db_session()
        new_sub = Subscription(
            user_email=sub_data.user_email,
            status="active",
            subscription_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=30),
        )
        db.add(new_sub)
        db.commit()
        db.close()

        return jsonify({
            "message": "Fake subscription created",
            "user_email": sub_data.user_email
        }), 201
    except ValidationError as e:
        return jsonify({"error": "Invalid data", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Fake subscription error: {e}")
        return jsonify({"error": "Failed to create fake subscription"}), 500

@app.route("/is-premium/<user_email>", methods=["GET"])
def is_premium(user_email):
    db = db_session()
    subscription = db.query(Subscription).filter_by(user_email=user_email).first()
    db.close()
    if subscription and subscription.status == "active":
        return jsonify({"is_premium": True})
    return jsonify({"is_premium": False})


def run_app():
    init_db()
    app.run(host="0.0.0.0", port=5003, debug=True)


if __name__ == "__main__":
    run_app()
