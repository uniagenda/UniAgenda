from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chave_secreta_uniagenda'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/uniagenda.sqlite'

    @app.template_filter('formata_data')
    def formata_data(data_iso):
        from datetime import datetime
        try:
            return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return data_iso  # fallback
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'uniagendaunivesp@gmail.com'
    app.config['MAIL_PASSWORD'] = 'pwhhizzxfeqxwdiw'

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app
