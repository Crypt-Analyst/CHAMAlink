from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import current_user, login_required
from app.models.two_factor import TwoFactorCode
from app.models.user import User
from app import db
import random
from datetime import datetime, timedelta

bp = Blueprint('two_factor', __name__, url_prefix='/2fa')

@bp.route('/send', methods=['POST'])
@login_required
def send_2fa():
    if not (current_user.is_founder or current_user.role == 'it'):
        return '', 403
    code = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=10)
    tf = TwoFactorCode(user_id=current_user.id, code=code, expires_at=expires)
    db.session.add(tf)
    db.session.commit()
    # TODO: Integrate with email/SMS provider
    print(f"2FA code for {current_user.email}: {code}")
    flash('A 2FA code has been sent to your email.')
    return redirect(url_for('two_factor.verify_2fa'))

@bp.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_2fa():
    if request.method == 'POST':
        code = request.form.get('code')
        tf = TwoFactorCode.query.filter_by(user_id=current_user.id, code=code, used=False).first()
        if tf and tf.is_valid():
            tf.used = True
            db.session.commit()
            session['2fa_verified'] = True
            flash('2FA verification successful.')
            return redirect(url_for('founder.dashboard'))
        flash('Invalid or expired code.')
    return render_template('two_factor/verify.html')
