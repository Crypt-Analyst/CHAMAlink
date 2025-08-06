from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
import psutil, os, time

system_health_bp = Blueprint('system_health', __name__, url_prefix='/system-health')

@system_health_bp.route('/')
@login_required
def dashboard():
    if not (current_user.is_founder or current_user.role == 'it'):
        return '', 403
    return render_template('system_health/dashboard.html')

@system_health_bp.route('/api/metrics')
@login_required
def metrics():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    uptime = time.time() - psutil.boot_time()
    return jsonify({
        'cpu': cpu,
        'memory': mem,
        'disk': disk,
        'uptime': uptime
    })
