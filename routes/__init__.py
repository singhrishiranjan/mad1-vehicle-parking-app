from .routes import routes_bp

def register_routes(app):
    app.register_blueprint(routes_bp)
