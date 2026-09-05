import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User
from seed_data import seed_database

def create_app(config_class=Config, auto_seed=True):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.main_routes import main_bp
    from routes.auth_routes import auth_bp
    from routes.student_routes import student_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # Custom Jinja filters
    @app.template_filter('badge_color')
    def badge_color_filter(importance):
        mapping = {
            'Critical': 'danger',
            'Recommended': 'primary',
            'Optional': 'secondary',
            'Beginner': 'success',
            'Intermediate': 'warning',
            'Advanced': 'danger',
            'Capstone': 'purple'
        }
        return mapping.get(importance, 'info')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    if auto_seed and not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()

    @app.cli.command('seed-db')
    def seed_db_command():
        seed_database(app)
        print("Database seeded!")

    return app


app = create_app(auto_seed=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(app)

    app.run(debug=True, port=5000)