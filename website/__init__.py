from flask import Flask
from .DB_connector import conn


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'

    from .public import public
    from .register_login import registerandlogin
    from .customer import customer
    from .agent import agent
    from .staff import staff

    app.register_blueprint(public, url_prefix='/')
    app.register_blueprint(registerandlogin, url_prefix='/')
    app.register_blueprint(customer, url_prefix='/')
    app.register_blueprint(staff, url_prefix='/')
    app.register_blueprint(agent, url_prefix='/')

    return app
