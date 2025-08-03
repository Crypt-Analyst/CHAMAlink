from flask import Blueprint, render_template

pwa_bp = Blueprint('pwa', __name__, url_prefix='/pwa')

@pwa_bp.route('/')
def pwa_home():
    """PWA landing page for mobile app users."""
    return render_template('pwa/home.html')
