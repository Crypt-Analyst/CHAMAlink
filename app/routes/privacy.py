from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User
from app import db
import io, csv

privacy_bp = Blueprint('privacy', __name__, url_prefix='/privacy')

@privacy_bp.route('/')
def privacy_policy():
    return render_template('privacy/policy.html')

@privacy_bp.route('/export', methods=['GET'])
@login_required
def export_data():
    user = User.query.get(current_user.id)
    data = {
        'username': user.username,
        'email': user.email,
        'phone_number': user.phone_number,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_of_birth': str(user.date_of_birth),
        'country': user.country_name,
        'city': user.city,
        'created_at': str(user.created_at),
    }
    output = io.StringIO()
    writer = csv.writer(output)
    for k, v in data.items():
        writer.writerow([k, v])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='mydata.csv')

@privacy_bp.route('/delete', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.','success')
    return redirect(url_for('main.home'))
