from flask import Flask
from core import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    from api import unified_routes, admin_routes
    app.register_blueprint(unified_routes.bp)
    app.register_blueprint(admin_routes.bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
