"""
Advanced Analytics Dashboard
==========================
Business intelligence and predictive analytics for CHAMAlink
"""

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from app.models import Chama, User, ChamaMember, SubscriptionPlan
from app.utils.permissions import admin_required
from app import db
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Advanced analytics dashboard for admins"""
    try:
        # Platform Statistics
        total_users = User.query.count()
        total_chamas = Chama.query.count()
        active_chamas = Chama.query.filter_by(status='active').count()
        total_members = ChamaMember.query.count()
        
        # Revenue Analytics
        subscription_revenue = db.session.query(
            func.sum(SubscriptionPlan.price).label('total')
        ).scalar() or 0
        
        # Growth Analytics (last 12 months)
        growth_data = []
        for i in range(12):
            month_start = datetime.now().replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            
            users_count = User.query.filter(
                User.created_at.between(month_start, month_end)
            ).count()
            
            chamas_count = Chama.query.filter(
                Chama.created_at.between(month_start, month_end)
            ).count()
            
            growth_data.append({
                'month': month_start.strftime('%Y-%m'),
                'users': users_count,
                'chamas': chamas_count
            })
        
        growth_data.reverse()
        
        # Chama Performance Analytics
        chama_performance = db.session.query(
            Chama.id,
            Chama.name,
            func.count(ChamaMember.id).label('member_count'),
            Chama.status,
            Chama.created_at
        ).outerjoin(ChamaMember).group_by(Chama.id).all()
        
        # User Engagement Analytics
        active_users_7d = User.query.filter(
            User.last_login >= datetime.now() - timedelta(days=7)
        ).count()
        
        active_users_30d = User.query.filter(
            User.last_login >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Subscription Analytics
        subscription_breakdown = db.session.query(
            SubscriptionPlan.name,
            func.count(SubscriptionPlan.id).label('count')
        ).group_by(SubscriptionPlan.name).all()
        
        # Geographic Distribution
        geographic_data = db.session.query(
            User.country_name,
            func.count(User.id).label('user_count')
        ).filter(User.country_name.isnot(None)).group_by(
            User.country_name
        ).order_by(func.count(User.id).desc()).limit(10).all()
        
        # Predictive Analytics - Growth Trends
        if len(growth_data) >= 3:
            recent_months = growth_data[-3:]
            avg_user_growth = sum(month['users'] for month in recent_months) / 3
            avg_chama_growth = sum(month['chamas'] for month in recent_months) / 3
            
            # Simple linear prediction for next month
            predicted_users = int(avg_user_growth * 1.1)  # 10% growth assumption
            predicted_chamas = int(avg_chama_growth * 1.1)
        else:
            predicted_users = 0
            predicted_chamas = 0
        
        analytics_data = {
            'platform_stats': {
                'total_users': total_users,
                'total_chamas': total_chamas,
                'active_chamas': active_chamas,
                'total_members': total_members,
                'subscription_revenue': subscription_revenue
            },
            'growth_data': growth_data,
            'chama_performance': [
                {
                    'id': perf.id,
                    'name': perf.name,
                    'member_count': perf.member_count,
                    'status': perf.status,
                    'age_days': (datetime.now() - perf.created_at).days
                } for perf in chama_performance
            ],
            'user_engagement': {
                'active_7d': active_users_7d,
                'active_30d': active_users_30d,
                'engagement_rate': round((active_users_7d / max(total_users, 1)) * 100, 2)
            },
            'subscription_breakdown': [
                {'name': sub.name, 'count': sub.count} 
                for sub in subscription_breakdown
            ],
            'geographic_data': [
                {'country': geo.country_name, 'users': geo.user_count}
                for geo in geographic_data
            ],
            'predictions': {
                'next_month_users': predicted_users,
                'next_month_chamas': predicted_chamas
            }
        }
        
        return render_template('analytics/dashboard.html', 
                             analytics=analytics_data)
        
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('analytics/dashboard.html', 
                             analytics={'error': str(e)})

@analytics_bp.route('/api/real-time-stats')
@login_required
@admin_required
def real_time_stats():
    """API endpoint for real-time statistics"""
    try:
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(hours=24)
        
        recent_users = User.query.filter(User.created_at >= yesterday).count()
        recent_chamas = Chama.query.filter(Chama.created_at >= yesterday).count()
        recent_logins = User.query.filter(User.last_login >= yesterday).count()
        
        # System health metrics
        total_users = User.query.count()
        active_chamas = Chama.query.filter_by(status='active').count()
        
        return jsonify({
            'success': True,
            'data': {
                'recent_activity': {
                    'new_users_24h': recent_users,
                    'new_chamas_24h': recent_chamas,
                    'active_users_24h': recent_logins
                },
                'system_health': {
                    'total_users': total_users,
                    'active_chamas': active_chamas,
                    'system_uptime': '99.9%',  # This would come from monitoring
                    'last_updated': datetime.now().isoformat()
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/export/<format>')
@login_required
@admin_required
def export_analytics(format):
    """Export analytics data in various formats"""
    try:
        # Get analytics data
        total_users = User.query.count()
        total_chamas = Chama.query.count()
        
        data = {
            'export_date': datetime.now().isoformat(),
            'platform_stats': {
                'total_users': total_users,
                'total_chamas': total_chamas
            }
        }
        
        if format.lower() == 'json':
            return jsonify(data)
        elif format.lower() == 'csv':
            # Convert to CSV format
            csv_data = f"Metric,Value\nTotal Users,{total_users}\nTotal Chamas,{total_chamas}\n"
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=analytics.csv'
            }
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/custom-dashboard')
@login_required
@admin_required
def custom_dashboard():
    """Custom dashboard builder"""
    return render_template('analytics/custom_dashboard.html')

@analytics_bp.route('/api/widget-data/<widget_type>')
@login_required
@admin_required
def widget_data(widget_type):
    """API endpoint for custom dashboard widgets"""
    try:
        if widget_type == 'user_growth':
            # User growth widget data
            data = []
            for i in range(30):
                date = datetime.now() - timedelta(days=i)
                count = User.query.filter(
                    func.date(User.created_at) == date.date()
                ).count()
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            return jsonify({'success': True, 'data': data})
            
        elif widget_type == 'chama_status':
            # Chama status distribution
            status_data = db.session.query(
                Chama.status,
                func.count(Chama.id).label('count')
            ).group_by(Chama.status).all()
            
            data = [{'status': s.status, 'count': s.count} for s in status_data]
            return jsonify({'success': True, 'data': data})
            
        elif widget_type == 'revenue_trend':
            # Revenue trend (placeholder - would integrate with payment system)
            data = [
                {'month': '2024-01', 'revenue': 15000},
                {'month': '2024-02', 'revenue': 18000},
                {'month': '2024-03', 'revenue': 22000},
            ]
            return jsonify({'success': True, 'data': data})
            
        else:
            return jsonify({'success': False, 'error': 'Unknown widget type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
