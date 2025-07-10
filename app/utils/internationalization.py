"""
Multi-language and theme support for ChamaLink
"""

from flask import session, request, current_app
import os
import json

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'sw': 'Kiswahili',
    'fr': 'Français',
    'ar': 'العربية'
}

# Supported themes
SUPPORTED_THEMES = {
    'light': 'Light Theme',
    'dark': 'Dark Theme',
    'blue': 'Blue Theme',
    'green': 'Green Theme'
}

# Supported fonts
SUPPORTED_FONTS = {
    'default': 'Default',
    'arial': 'Arial',
    'helvetica': 'Helvetica',
    'times': 'Times New Roman',
    'georgia': 'Georgia',
    'verdana': 'Verdana'
}

def get_current_language():
    """Get current language from session or default"""
    return session.get('language', 'en')

def set_language(language_code):
    """Set language in session"""
    if language_code in SUPPORTED_LANGUAGES:
        session['language'] = language_code
        return True
    return False

def get_current_theme():
    """Get current theme from session or default"""
    return session.get('theme', 'light')

def set_theme(theme_name):
    """Set theme in session"""
    if theme_name in SUPPORTED_THEMES:
        session['theme'] = theme_name
        return True
    return False

def get_current_font():
    """Get current font from session or default"""
    return session.get('font', 'default')

def set_font(font_name):
    """Set font in session"""
    if font_name in SUPPORTED_FONTS:
        session['font'] = font_name
        return True
    return False

def load_translations(language_code):
    """Load translations for a specific language"""
    translations_file = os.path.join(
        current_app.root_path, 
        'translations', 
        f'{language_code}.json'
    )
    
    try:
        with open(translations_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to English
        fallback_file = os.path.join(
            current_app.root_path, 
            'translations', 
            'en.json'
        )
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

def t(key, **kwargs):
    """Translate a key to current language"""
    language = get_current_language()
    translations = load_translations(language)
    
    # Get translation or fallback to key
    translation = translations.get(key, key)
    
    # Format with kwargs if provided
    if kwargs:
        try:
            translation = translation.format(**kwargs)
        except KeyError:
            pass
    
    return translation

# Template filter for translations
def translate_filter(key, **kwargs):
    """Template filter for translations"""
    return t(key, **kwargs)

def init_internationalization(app):
    """Initialize internationalization features"""
    
    @app.template_filter('t')
    def translate_template_filter(key, **kwargs):
        return t(key, **kwargs)
    
    @app.context_processor
    def inject_language_vars():
        return {
            'current_language': get_current_language(),
            'current_theme': get_current_theme(),
            'current_font': get_current_font(),
            'supported_languages': SUPPORTED_LANGUAGES,
            'supported_themes': SUPPORTED_THEMES,
            'supported_fonts': SUPPORTED_FONTS,
            't': t
        }
    
    @app.before_request
    def before_request():
        # Auto-detect language from browser if not set
        if 'language' not in session and request.headers.get('Accept-Language'):
            browser_lang = request.headers.get('Accept-Language', '').split(',')[0].split('-')[0]
            if browser_lang in SUPPORTED_LANGUAGES:
                session['language'] = browser_lang
