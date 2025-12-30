from __future__ import annotations

from flask import Blueprint

from .admin_conversation_routes import admin_conversation_bp
from .auth_routes import auth_bp
from .conversation_routes import conversation_bp
from .health import health_bp
from .password_routes import password_bp
from .user_routes import user_bp

api_bp = Blueprint("api", __name__, url_prefix="/api")
api_bp.register_blueprint(admin_conversation_bp)
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(conversation_bp)
api_bp.register_blueprint(user_bp)
api_bp.register_blueprint(password_bp)
api_bp.register_blueprint(health_bp)

__all__ = ["api_bp"]
