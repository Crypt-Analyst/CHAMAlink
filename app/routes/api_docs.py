from flask import Blueprint, render_template

api_docs_bp = Blueprint('api_docs', __name__)

@api_docs_bp.route('/api/docs')
def api_docs():
    return render_template('api_docs/swagger_ui.html')
