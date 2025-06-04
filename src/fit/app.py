from flask import Flask
from .database import init_db
from .services.fitness_data_init import init_fitness_data

# Import blueprints
from .blueprints.users import user_bp
from .blueprints.auth import auth_bp
from .blueprints.fitness import fitness_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints with URL prefixes
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(fitness_bp, url_prefix="/fitness")

    @app.route("/health")
    def health():
        return {"status": "UP"}

    return app

# 👇 This allows `from src.fit.app import app` to work:
app = create_app()

def run_app():
    init_db()
    init_fitness_data()
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run_app()
