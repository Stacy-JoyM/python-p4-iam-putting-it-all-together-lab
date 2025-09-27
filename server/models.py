from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash


from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

      # Exclude password hash from serialization
    serialize_rules = ('-recipes.user', '-_password_hash')


    #attributes 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=True)
    image_url = db.Column(db.String, nullable=True)
    bio = db.Column(db.String)

    # One-to-Many: User → Recipe
    recipes = db.relationship("Recipe", back_populates="user", cascade="all, delete-orphan")

    # --- Password Handling ---
     # Prevent direct access to password hash
    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes are not viewable.")

    # Use this setter to hash the password
    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = generate_password_hash(password)

    # Authenticate with plain password
    def authenticate(self, password):
        return check_password_hash(self._password_hash, password)
    
    # --- Validations ---
    @validates("username")
    def validate_username(self, key, value):
        if not value or not value.strip():
            raise ValueError("Username must be present.")
        return value

    def __repr__(self):
        return f"<User {self.username}>"

    

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    serialize_rules = ('-user.recipes',)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) #Foreign key for user"

    # Relationship back to User
    user = db.relationship("User", back_populates="recipes")
    


     # --- Validation ---
    @validates("title")
    def validate_title(self, key, value):
        if not value or value.strip() == "":
            raise ValueError("Recipe title must be provided.")
        return value

    @validates("instructions")
    def validate_instructions(self, key, value):
        if not value or len(value.strip()) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return value
    
    @validates("user_id")
    def validate_user_id(self, key, value):
        if not value:
            raise ValueError("Recipe must be associated with a User.")
        return value

    #Additional database constraints to ensure minutes are positive integer 
    __table_args__ = (
        CheckConstraint("minutes_to_complete > 0", name="minutes_positive_check"),
    ) 

    def __repr__(self):
        return f"<Recipe {self.title}, by User {self.user_id}>"
    





    
