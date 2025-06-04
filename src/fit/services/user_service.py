from ..models_dto import UserSchema, UserResponseSchema, UserProfileSchema, UserProfileResponseSchema
from ..models_db import UserModel
from ..database import db_session
from typing import List, Optional
import random
import string
import hashlib

def generate_random_password(length=10):
    """Generate a random password of specified length"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(user: UserSchema) -> UserResponseSchema:
    """
    Create a new user with a random password and persist it to the database
    """
    random_password = generate_random_password()
    hashed_password = hash_password(random_password)
    
    db_user = UserModel(
        email=user.email,
        name=user.name,
        role=user.role,
        password_hash=hashed_password
    )
    
    db = db_session()
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
    
    response = UserResponseSchema(
        email=user.email,
        name=user.name,
        role=user.role,
        password=random_password
    )
    
    return response

def get_all_users() -> List[UserSchema]:
    """
    Retrieve all users from the database
    """
    db = db_session()
    try:
        db_users = db.query(UserModel).all()
        

        return [
            UserSchema(
                email=db_user.email,
                name=db_user.name,
                role=db_user.role
            )
            for db_user in db_users
        ]
    finally:
        db.close()

def update_user_profile(email: str, profile: UserProfileSchema) -> Optional[UserProfileResponseSchema]:
    """
    Update user profile with weight, height, and fitness goal
    """
    db = db_session()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None
            
    
        user.weight = profile.weight
        user.height = profile.height
        user.fitness_goal = profile.fitness_goal
        user.onboarded = "true"
        
        db.commit()
        db.refresh(user)
        
        return UserProfileResponseSchema(
            email=user.email,
            name=user.name,
            weight=user.weight,
            height=user.height,
            fitness_goal=user.fitness_goal,
            onboarded=user.onboarded
        )
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_user_profile(email: str) -> Optional[UserProfileResponseSchema]:
    """
    Get user profile information
    """
    db = db_session()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None
            
        return UserProfileResponseSchema(
            email=user.email,
            name=user.name,
            weight=user.weight,
            height=user.height,
            fitness_goal=user.fitness_goal,
            onboarded=user.onboarded
        )
    finally:
        db.close()
