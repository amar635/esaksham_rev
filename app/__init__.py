import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from app.classes.helper import generate_rsa_key_pair
from app.db import db
from app.models import State_UT,District,Block,User
from app.routes.routes import blp as routesBlueprint
from app.routes.auth import blp as authBlueprint
from app.apis.api import blp as apiBlueprint
from app.apis.lms import blp as apilmsBlueprint
from app.apis.lrs import blp as apilrsBlueprint


def create_app():
    load_dotenv()
    app = Flask(__name__)

    # App Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # SCORM Folders
    directory_path = os.path.dirname(__file__)
    app.config['UPLOAD_FOLDER'] = os.path.join(directory_path,'static/uploads')
    app.config['SCORM_FOLDER'] = os.path.join(directory_path,'static/scorm_packages')
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SCORM_FOLDER'], exist_ok=True)

    # DB Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    public_key_pem, private_key_pem = generate_rsa_key_pair()
    app.config['PUBLIC_KEY'] = public_key_pem
    app.config['PRIVATE_KEY'] = private_key_pem

    # Initialize
    # db.init_app(app)
    # migrate = Migrate(app, db)
    # csrf = CSRFProtect(app)
    # login_manager=LoginManager(app)
    # # create_db(app)

    # @login_manager.user_loader
    # def load_user(user_id):
    #     return User.get_user_by_id(user_id)

    # login_manager.login_view = "auth.login"
    # login_manager.login_message = "Access is restricted. Please login"
    # login_manager.login_message_category = "info"
    # Register Blueprint
    app.register_blueprint(routesBlueprint)
    app.register_blueprint(authBlueprint)
    app.register_blueprint(apiBlueprint)
    app.register_blueprint(apilmsBlueprint)
    app.register_blueprint(apilrsBlueprint)
    from app.routes.admin import blp as adminBlueprint
    app.register_blueprint(adminBlueprint)
    return app