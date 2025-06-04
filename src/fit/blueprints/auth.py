from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from ..models_dto import LoginSchema, TokenSchema
from ..services.auth_service import authenticate_user, jwt_required,decode_token,create_access_token
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login: validates credentials and returns JWT token.
    """
    try:
        data = request.get_json()
        login_data = LoginSchema.model_validate(data)
        
        user = authenticate_user(login_data.email, login_data.password)
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        token = create_access_token({"sub":user.email,"role":user.role}) 
        return jsonify({"access_token": token}), 200
        
    except ValidationError as e:
        return jsonify({"error": "Invalid login data", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "Login failed", "details": str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    User logout endpoint: revoke token or just notify client to discard token.
    Implementation depends on your token revocation strategy.
    """
    try:
        token = request.headers.get("Authorization").split()[1]
        decode_token(token)
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Logout failed", "details": str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh_token():
    """
    Refresh the JWT token. Requires valid current token.
    """
    try:
        user_email = g.user_email
        new_token = create_access_token(user_email, expires_minutes=30)
        return jsonify({"access_token": new_token}), 200
    except Exception as e:
        return jsonify({"error": "Token refresh failed", "details": str(e)}), 500
