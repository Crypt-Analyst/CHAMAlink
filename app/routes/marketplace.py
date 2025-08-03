from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')

@marketplace_bp.route('/')
def marketplace_home():
    """Marketplace home page: list all products/services."""
    # TODO: Query products from DB
    return render_template('marketplace/home.html', products=[])

@marketplace_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """View details of a single product/service."""
    # TODO: Query product by ID
    return render_template('marketplace/detail.html', product=None)

@marketplace_bp.route('/vendor/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Vendor adds a new product/service."""
    if request.method == 'POST':
        # TODO: Save product to DB
        flash('Product submitted for review.', 'success')
        return redirect(url_for('marketplace.marketplace_home'))
    return render_template('marketplace/add.html')

@marketplace_bp.route('/admin/approve/<int:product_id>')
@login_required
def approve_product(product_id):
    """Admin approves a product listing."""
    # TODO: Approve product in DB
    flash('Product approved.', 'success')
    return redirect(url_for('marketplace.marketplace_home'))

@marketplace_bp.route('/api/list')
def api_list_products():
    """API: List all products/services."""
    # TODO: Return products as JSON
    return jsonify({'products': []})
