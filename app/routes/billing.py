from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.subscription import SubscriptionPlan, UserSubscription
from app import db

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/pricing')
def pricing():
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('billing/pricing.html', plans=plans)

@billing_bp.route('/subscribe/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def subscribe(plan_id):
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        # Simulate payment and create subscription
        sub = Subscription(user_id=current_user.id, plan_id=plan.id, status='active', payment_method=payment_method)
        db.session.add(sub)
        db.session.commit()
        flash(f'Subscription successful! Payment method: {payment_method}', 'success')
        return redirect(url_for('billing.manage'))
    return render_template('billing/subscribe.html', plan=plan)

@billing_bp.route('/billing/manage')
@login_required
def manage():
    subs = Subscription.query.filter_by(user_id=current_user.id).all()
    return render_template('billing/manage.html', subscriptions=subs)
