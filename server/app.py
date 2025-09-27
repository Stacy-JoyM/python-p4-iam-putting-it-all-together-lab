#!/usr/bin/env python3

from flask import request, session, jsonify, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api, bcrypt 
from models import User, Recipe
from werkzeug.security import generate_password_hash, check_password_hash 



class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        errors = []

        if not username:
            errors.append("Username is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        # Add additional validation as needed

        if errors:
            return {'errors': errors}, 422

        try:
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password_hash = password 

            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio
            }, 201

        except Exception as e:
            return {"errors": [str(e)]}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': 'Unauthorized'}, 401

        user = User.query.get(user_id)

        if not user:
            return {'error': 'User not found'}, 401

        return {
            "id": user.id,
            "username": user.username,
            "image_url": user.image_url,
            "bio": user.bio
        }, 200




class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):  # ✅ Use authenticate method
            session['user_id'] = user.id
            return user.to_dict(), 200
        
        return {"error": "Invalid username or password"}, 401
    
class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        
        session.pop('user_id', None)
        return {}, 204
    
class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        # If logged in, return recipes of that user
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        # Use to_dict (or SerializerMixin) to serialize
        return [recipe.to_dict() for recipe in recipes], 200
    
    def post(self):
        # 1. Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json()

        try:
            # 2. Create new recipe, associate with logged-in user
            new_recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )

            # 3. Add and commit to the database
            db.session.add(new_recipe)
            db.session.commit()

            # 4. Return serialized data including nested user
            response_data = new_recipe.to_dict(rules=('-user.recipes',))  # Optional: avoid circular nesting
            return response_data, 201

        except (ValueError, KeyError) as e:
            # 5. Handle validation or missing data errors
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)