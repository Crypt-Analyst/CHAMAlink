"""
Routes for user preferences: language, theme, font settings
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from flask_login import login_required, current_user
from app.utils.internationalization import (
    set_language, set_theme, set_font,
    get_current_language, get_current_theme, get_current_font,
    SUPPORTED_LANGUAGES, SUPPORTED_THEMES, SUPPORTED_FONTS
)
from app import db

preferences_bp = Blueprint('preferences', __name__, url_prefix='/preferences')

@preferences_bp.route('/language/<language_code>', methods=['GET', 'POST'])
def change_language(language_code):
    """Change language and redirect back"""
    if set_language(language_code):
        # If user is logged in, save to database
        if current_user.is_authenticated:
            try:
                current_user.preferred_language = language_code
                db.session.commit()
            except:
                db.session.rollback()
    
    # Return JSON response for AJAX requests
    if request.method == 'POST':
        return jsonify({'success': True, 'language': language_code})
    
    # Redirect back to previous page or dashboard for GET requests
    return redirect(request.referrer or url_for('main.dashboard'))

@preferences_bp.route('/theme/<theme_name>')
def change_theme(theme_name):
    """Change theme and redirect back"""
    if set_theme(theme_name):
        # If user is logged in, save to database
        if current_user.is_authenticated:
            try:
                current_user.preferred_theme = theme_name
                db.session.commit()
            except:
                db.session.rollback()
    
    # Redirect back to previous page or dashboard
    return redirect(request.referrer or url_for('main.dashboard'))

@preferences_bp.route('/font/<font_name>')
def change_font(font_name):
    """Change font and redirect back"""
    if set_font(font_name):
        # If user is logged in, save to database
        if current_user.is_authenticated:
            try:
                current_user.preferred_font = font_name
                db.session.commit()
            except:
                db.session.rollback()
    
    # Redirect back to previous page or dashboard
    return redirect(request.referrer or url_for('main.dashboard'))

@preferences_bp.route('/api/set', methods=['POST'])
@login_required
def set_preferences_api():
    """API endpoint to set multiple preferences"""
    try:
        data = request.get_json()
        language = data.get('language')
        theme = data.get('theme')
        font = data.get('font')
        
        success = True
        messages = []
        
        # Update language
        if language and set_language(language):
            current_user.preferred_language = language
            messages.append(f"Language changed to {SUPPORTED_LANGUAGES.get(language, language)}")
        elif language:
            success = False
            messages.append("Invalid language")
        
        # Update theme
        if theme and set_theme(theme):
            current_user.preferred_theme = theme
            messages.append(f"Theme changed to {SUPPORTED_THEMES.get(theme, theme)}")
        elif theme:
            success = False
            messages.append("Invalid theme")
        
        # Update font
        if font and set_font(font):
            current_user.preferred_font = font
            messages.append(f"Font changed to {SUPPORTED_FONTS.get(font, font)}")
        elif font:
            success = False
            messages.append("Invalid font")
        
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully',
                'details': messages
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to update some preferences',
                'details': messages
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating preferences: {str(e)}'
        }), 500

@preferences_bp.route('/api/get')
@login_required
def get_preferences_api():
    """API endpoint to get current preferences"""
    return jsonify({
        'language': get_current_language(),
        'theme': get_current_theme(),
        'font': get_current_font(),
        'supported': {
            'languages': SUPPORTED_LANGUAGES,
            'themes': SUPPORTED_THEMES,
            'fonts': SUPPORTED_FONTS
        }
    })

@preferences_bp.route('/')
@preferences_bp.route('')
@login_required
def preferences_page():
    """Preferences management page"""
    return render_template('preferences/index.html',
                         current_language=get_current_language(),
                         current_theme=get_current_theme(),
                         current_font=get_current_font(),
                         supported_languages=SUPPORTED_LANGUAGES,
                         supported_themes=SUPPORTED_THEMES,
                         supported_fonts=SUPPORTED_FONTS)
