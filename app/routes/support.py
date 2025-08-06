from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db

support_bp = Blueprint('support', __name__, url_prefix='/support')

@support_bp.route('/', methods=['GET', 'POST'])
@login_required
def ticket():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        # TODO: Store or send ticket to support system
        flash('Your support request has been submitted.', 'success')
        return redirect(url_for('support.ticket'))
    return render_template('support/ticket.html')
