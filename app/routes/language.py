from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_babel import gettext as _
from flask_login import login_required

language_bp = Blueprint('language', __name__, url_prefix='/language')

@language_bp.route('/')
def language_settings():
    """Language selection page."""
    # TODO: List available languages
    return render_template('language/settings.html', languages=['en', 'sw', 'fr'])

@language_bp.route('/set/<lang_code>')
def set_language(lang_code):
    """Set user language preference."""
    # TODO: Save language preference (session or DB)
    flash(_('Language changed.'), 'success')
    return redirect(url_for('language.language_settings'))
