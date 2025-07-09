from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.enterprise import EnterpriseSubscriptionPlan, EnterpriseUserSubscription, EnterpriseSubscriptionPayment, PlanType
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import uuid

subscription_new_bp = Blueprint("subscription_new", __name__)

@subscription_new_bp.route("/pricing")
def pricing():
    """Display pricing plans"""
    plans = EnterpriseSubscriptionPlan.query.filter_by(is_active=True).order_by(EnterpriseSubscriptionPlan.price_monthly).all()
    return render_template("subscription/pricing.html", plans=plans)

@subscription_new_bp.route("/enterprise/contact")
def enterprise_contact():
    """Enterprise contact form"""
    return render_template("subscription/enterprise_contact.html")
