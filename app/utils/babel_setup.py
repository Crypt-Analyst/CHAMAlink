from flask_babel import Babel

def init_babel(app):
    babel = Babel(app)
    @babel.localeselector
    def get_locale():
        return app.config.get('BABEL_DEFAULT_LOCALE', 'en')
    return babel
