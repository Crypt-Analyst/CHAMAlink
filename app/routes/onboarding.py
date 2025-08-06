from flask import Blueprint, render_template
from flask_login import login_required

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/welcome', endpoint='welcome')
def welcome():
    return render_template('onboarding/welcome.html')

@onboarding_bp.route('/faq')
def faq():
    return render_template('onboarding/faq.html')
