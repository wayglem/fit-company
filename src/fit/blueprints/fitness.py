from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from ..models_dto import WodResponseSchema, WodExerciseSchema, MuscleGroupImpact
from ..services.wod_service import (
    get_all_wods,
    get_wod_by_id,
    create_wod,
    update_wod,
    delete_wod
)
from ..services.auth_service import jwt_required, admin_required
from ..services.wod_service import WODService 

fitness_bp = Blueprint('fitness', __name__)

wod_service = WODService()  

@fitness_bp.route('/wods', methods=['GET'])
@jwt_required
def list_wods():
    try:
        wods = get_all_wods()
        return jsonify([wod.model_dump() for wod in wods]), 200
    except Exception as e:
        return jsonify({"error": "Error fetching workouts", "details": str(e)}), 500

@fitness_bp.route('/wods/<int:wod_id>', methods=['GET'])
@jwt_required
def get_wod(wod_id):
    try:
        wod = get_wod_by_id(wod_id)
        if not wod:
            return jsonify({"error": "Workout not found"}), 404
        return jsonify(wod.model_dump()), 200
    except Exception as e:
        return jsonify({"error": "Error fetching workout", "details": str(e)}), 500

@fitness_bp.route('/wods', methods=['POST'])
@admin_required
def create_wod_endpoint():
    try:
        wod_data = request.get_json()
        wod = WodResponseSchema.model_validate(wod_data)
        created_wod = create_wod(wod)
        return jsonify(created_wod.model_dump()), 201
    except ValidationError as e:
        return jsonify({"error": "Invalid workout data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error creating workout", "details": str(e)}), 500

@fitness_bp.route('/wods/<int:wod_id>', methods=['PUT'])
@admin_required
def update_wod_endpoint(wod_id):
    try:
        wod_data = request.get_json()
        wod = WodResponseSchema.model_validate(wod_data)
        updated_wod = update_wod(wod_id, wod)
        if not updated_wod:
            return jsonify({"error": "Workout not found"}), 404
        return jsonify(updated_wod.model_dump()), 200
    except ValidationError as e:
        return jsonify({"error": "Invalid workout data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Error updating workout", "details": str(e)}), 500

@fitness_bp.route('/wods/<int:wod_id>', methods=['DELETE'])
@admin_required
def delete_wod_endpoint(wod_id):
    try:
        success = delete_wod(wod_id)
        if not success:
            return jsonify({"error": "Workout not found"}), 404
        return jsonify({"message": "Workout deleted"}), 200
    except Exception as e:
        return jsonify({"error": "Error deleting workout", "details": str(e)}), 500

@fitness_bp.route('/wod/generate', methods=['GET'])
@jwt_required
def generate_wod():
    try:
        user_email = g.user_email 
        wod = wod_service.request_wod(user_email)

        # Format response
        response_data = []
        for exercise, muscle_groups in wod:
            response_data.append({
                "exercise": {
                    "id": exercise.id,
                    "name": exercise.name,
                    "description": exercise.description,
                    "difficulty": exercise.difficulty,
                    "equipment": exercise.equipment,
                    "instructions": exercise.instructions,
                },
                "muscle_groups": [
                    {
                        "id": mg.id,
                        "name": mg.name,
                        "body_part": mg.body_part,
                        "description": mg.description,
                        "is_primary": is_primary
                    } for mg, is_primary in muscle_groups
                ]
            })

        return jsonify({"wod": response_data}), 200
    except Exception as e:
        return jsonify({"error": "Failed to generate WOD", "details": str(e)}), 500
