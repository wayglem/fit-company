from flask import Flask, request, jsonify, g
from pydantic import ValidationError
from .models_dto import UserSchema, UserResponseSchema, LoginSchema, TokenSchema, UserProfileSchema, UserProfileResponseSchema, WodResponseSchema, WodExerciseSchema, MuscleGroupImpact
from .services.user_service import create_user as create_user_service
from .services.user_service import get_all_users as get_all_users_service
from .services.user_service import update_user_profile, get_user_profile
from .services.auth_service import authenticate_user, create_access_token, admin_required, jwt_required
from .database import init_db, db_session
from .models_db import UserModel
from .services.fitness_data_init import init_fitness_data
from .services.fitness_service import (
    get_all_exercises, get_exercise_by_id, get_exercises_by_muscle_group
)
from .services.fitness_coach_service import calculate_intensity, insert_exercise_history, request_wod
import datetime
import os
import random

app = Flask(__name__)

BOOTSTRAP_KEY = os.environ.get("BOOTSTRAP_KEY", "bootstrap-secret-key")

@app.route("/health")
def health():
    return {"status": "UP"}

@app.route("/users", methods=["POST"])
@admin_required
def create_user():
    try:
        user_data = request.get_json()
        user = UserSchema.model_validate(user_data)
        created_user = create_user_service(user)
        return jsonify(created_user.model_dump()), 201
    except ValidationError as e:
        return jsonify({"error": "Invalid user data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error creating user", "details": str(e)}), 500

@app.route("/users", methods=["GET"])
@admin_required
def get_all_users():
    try:
        users = get_all_users_service()
        return jsonify([user.model_dump() for user in users]), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving users", "details": str(e)}), 500

@app.route("/bootstrap/admin", methods=["POST"])
def create_bootstrap_admin():
    try:
        # This endpoint should be secured with a special bootstrap key
        bootstrap_key = request.headers.get('X-Bootstrap-Key')
        if not bootstrap_key or bootstrap_key != BOOTSTRAP_KEY:
            return jsonify({"error": "Invalid bootstrap key"}), 401
            
        # Check if admin already exists to prevent multiple bootstraps
        db = db_session()
        admin_exists = db.query(UserModel).filter(UserModel.role == "admin").first() is not None
        db.close()
        
        if admin_exists:
            return jsonify({"error": "Admin user already exists"}), 409
            
        # Create admin user
        admin_data = request.get_json()
        admin_data["role"] = "admin"  # Ensure role is admin
        
        admin_user = UserSchema.model_validate(admin_data)
        created_admin = create_user_service(admin_user)
        
        return jsonify(created_admin.model_dump()), 201
        
    except ValidationError as e:
        return jsonify({"error": "Invalid admin data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error creating admin", "details": str(e)}), 500

@app.route("/profile/onboarding", methods=["POST"])
@jwt_required
def onboard_user():
    try:
        # Get user email from the JWT token (set by the jwt_required decorator)
        user_email = g.user_email
        
        # Parse and validate the profile data
        profile_data = request.get_json()
        profile = UserProfileSchema.model_validate(profile_data)
        
        # Update the user's profile
        updated_profile = update_user_profile(user_email, profile)
        if not updated_profile:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(updated_profile.model_dump()), 200
        
    except ValidationError as e:
        return jsonify({"error": "Invalid profile data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error updating profile", "details": str(e)}), 500

@app.route("/profile", methods=["GET"])
@jwt_required
def get_profile():
    try:
        # Get user email from the JWT token
        user_email = g.user_email
        
        # Get the user's profile
        profile = get_user_profile(user_email)
        if not profile:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify(profile.model_dump()), 200
        
    except Exception as e:
        return jsonify({"error": "Error retrieving profile", "details": str(e)}), 500

@app.route("/oauth/token", methods=["POST"])
def login():
    try:
        # Check if content type is application/x-www-form-urlencoded (OAuth standard)
        content_type = request.headers.get('Content-Type', '')
        if 'application/x-www-form-urlencoded' in content_type:
            login_data = {
                "email": request.form.get("username"),  # OAuth uses 'username' 
                "password": request.form.get("password")
            }
        else:  # Fallback to JSON
            login_data = request.get_json()
            
        login_schema = LoginSchema.model_validate(login_data)
        
        user = authenticate_user(login_schema.email, login_schema.password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create access token with standard OAuth claims
        access_token_expires = datetime.timedelta(minutes=30)
        token_data = {
            "sub": user.email,
            "name": user.name,
            "role": user.role,
            "iss": "fit-api", 
            "iat": datetime.datetime.now(datetime.UTC), 
        }
        
        access_token = create_access_token(
            data=token_data, 
            expires_delta=access_token_expires
        )
        
        token = TokenSchema(
            access_token=access_token,
            token_type="bearer"
        )
        
        # Include onboarding status in response
        response_data = token.model_dump()
        response_data["onboarded"] = user.onboarded
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        return jsonify({"error": "Invalid login data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error logging in", "details": str(e)}), 500

@app.route("/fitness/exercises", methods=["GET"])
def get_exercises():
    try:
        muscle_group_id = request.args.get("muscle_group_id")
        if muscle_group_id:
            # Get exercises for a specific muscle group
            exercises = get_exercises_by_muscle_group(int(muscle_group_id))
        else:
            # Get all exercises
            exercises = get_all_exercises()
        return jsonify([ex.model_dump() for ex in exercises]), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving exercises", "details": str(e)}), 500

@app.route("/fitness/exercises/<int:exercise_id>", methods=["GET"])
def get_exercise(exercise_id):
    try:
        exercise = get_exercise_by_id(exercise_id)
        if not exercise:
            return jsonify({"error": "Exercise not found"}), 404
        return jsonify(exercise.model_dump()), 200
    except Exception as e:
        return jsonify({"error": "Error retrieving exercise", "details": str(e)}), 500

@app.route("/fitness/wod", methods=["GET"])
@jwt_required
def get_wod():
    try:
        # Get the workout exercises with their muscle groups
        exercises_with_muscles = request_wod(g.user_email)
        
        # Convert to response schema
        wod_exercises = []
        for exercise, muscle_groups in exercises_with_muscles:
            # Create muscle group impact objects
            muscle_impacts = [
                MuscleGroupImpact(
                    id=mg.id,
                    name=mg.name,
                    body_part=mg.body_part,
                    is_primary=is_primary,
                    # Higher intensity for primary muscle groups
                    intensity=calculate_intensity(exercise.difficulty) * (1.2 if is_primary else 0.8)
                )
                for mg, is_primary in muscle_groups
            ]
            
            # Create exercise object
            wod_exercise = WodExerciseSchema(
                id=exercise.id,
                name=exercise.name,
                description=exercise.description,
                difficulty=exercise.difficulty,
                muscle_groups=muscle_impacts,
                suggested_weight=random.uniform(5.0, 50.0),  # Random weight between 5 and 50 kg
                suggested_reps=random.randint(8, 15)  # Random reps between 8 and 15
            )
            wod_exercises.append(wod_exercise)
        
        for wod_exercise in wod_exercises:
            # Insert each exercise into the history
            insert_exercise_history(g.user_email, wod_exercise.id)

        response = WodResponseSchema(
            exercises=wod_exercises,
            generated_at=datetime.datetime.now(datetime.UTC).isoformat()
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify({"error": "Error generating workout of the day", "details": str(e)}), 500

def run_app():
    """Entry point for the application script"""
    # Initialize the database before starting the app
    init_db()
    
    # Initialize fitness data
    init_fitness_data()
    
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run_app()

