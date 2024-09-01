# api/__init__.py

from flask import Flask, g, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
from api.routes.applicants import applicants_bp
from api.routes.schemes import schemes_bp
from api.routes.applications import applications_bp
from api.routes.auth import auth_bp  
from config import Config
from dal.database import Base  # Import your Base model

# Initialize extensions
ma = Marshmallow()
jwt = JWTManager()

from dotenv import load_dotenv
load_dotenv()
from environs import Env

# Load environment variables
DATABASE_URL = Env().str("DATABASE_URL", "DATABASE_URL is not set.") 
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    ma.init_app(app)
    jwt.init_app(app)

    # Register routes
    app.register_blueprint(applicants_bp)
    app.register_blueprint(schemes_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(auth_bp) 
    
    # Initialize SQLAlchemy session handling
    setup_db_session(app)

    # Error handler for Marshmallow validation errors
    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation_error(e):
        return jsonify({"errors": e.messages}), 400

    # Error handler for SQLAlchemy errors
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(e):
        # Rollback the session to prevent any potential side effects
        session = g.get('db_session')
        if session is not None:
            session.rollback()  # Properly rollback the session
        return jsonify({"error": "A database error occurred."}), 500

    # General error handler
    @app.errorhandler(Exception)
    def handle_generic_error(e):
        return jsonify({"error": str(e)}), 500
    
    return app

def setup_db_session(app):
    """Setup SQLAlchemy sessions for the app."""

    @app.before_request
    def create_session():
        """Create a new database session for a request."""
        g.db_session = SessionLocal() # Note: This is a normal session, not a scoped_session

    @app.teardown_appcontext
    def remove_session(exception=None):
        """Remove the database session after the request ends."""
        db_session = g.pop('db_session', None)
        if db_session is not None:
            db_session.close() # Use close() instead of remove() for regular session

# Ensure our database tables are created (Idempotent operation):
Base.metadata.create_all(bind=engine)