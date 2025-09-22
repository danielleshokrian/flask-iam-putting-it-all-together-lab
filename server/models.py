from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields, validates, ValidationError
from marshmallow.validate import Length, URL


from config import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    _password_hash = db.Column(db.String(128), nullable=False)
    image_url = db.Column(db.String, default='https://cdn.filestackcontent.com/default-image.png')
    bio = db.Column(db.String(240), default='This user prefers to keep an air of mystery about them.')
    recipes = db.relationship('Recipe', back_populates='user', cascade='all, delete-orphan')

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")
    
    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='recipes')
    instructions = db.Column(db.Text, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=Length(min=3, max=20))
    image_url = fields.Str()
    bio = fields.Str()
    password = fields.Str(load_only=True, required=True, validate=Length(min=6), error_messages={"required": "Password is required."})
    recipes = fields.Nested('RecipeSchema', many=True, dump_only=True)

    @validates ('username')
    def validate_username(self, value):
        if ' ' in value:
            raise ValidationError("Username cannot contain spaces.")
        

class RecipeSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=Length(min=1, max=100, error="Title must be between 1 and 100 characters." ))
    instructions = fields.Str(required=True, validate=Length(min=50, error="Instructions cannot be less than 50 characters."))
    minutes_to_complete = fields.Int(required=True)
    user_id = fields.Int(load_only=True, required=True)
    user = fields.Nested('UserSchema', only=['id', 'username'], dump_only=True)

    @validates('minutes_to_complete')
    def validate_minutes(self, value):
        if value <= 0:
            raise ValidationError("Minutes to complete must be a positive integer.")
