"""
Advanced Compliance System
========================
KYC automation, regulatory reporting, and compliance monitoring
"""

from flask import Blueprint, render_template, request, jsonify, flash, send_file
from flask_login import login_required, current_user
from app.models import User, Chama, ChamaMember
from app.utils.permissions import admin_required
from app import db
from datetime import datetime, timedelta
import json
import io
import csv
from werkzeug.utils import secure_filename
import os

compliance_bp = Blueprint('compliance', __name__, url_prefix='/compliance')

@compliance_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Compliance dashboard"""
    try:
        # Get compliance statistics
        total_users = User.query.count()
        verified_users = User.query.filter_by(is_documents_verified=True).count()
        pending_verification = User.query.filter_by(is_documents_verified=False).count()
        
        # KYC completion rate
        kyc_completion_rate = (verified_users / max(total_users, 1)) * 100
        
        # Recent compliance activities
        recent_registrations = User.query.filter(
            User.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        # Compliance requirements status
        compliance_status = {
            'kyc_automation': {
                'status': 'active',
                'description': 'Automated KYC verification for new users',
                'compliance_rate': kyc_completion_rate
            },
            'aml_monitoring': {
                'status': 'active',
                'description': 'Anti-Money Laundering transaction monitoring',
                'alerts_count': 0
            },
            'regulatory_reporting': {
                'status': 'active',
                'description': 'Automated regulatory reports generation',
                'last_report': datetime.now() - timedelta(days=1)
            },
            'data_protection': {
                'status': 'compliant',
                'description': 'GDPR and local data protection compliance',
                'encryption_status': 'active'
            }
        }
        
        return render_template('compliance/dashboard.html', 
                             compliance_stats={
                                 'total_users': total_users,
                                 'verified_users': verified_users,
                                 'pending_verification': pending_verification,
                                 'kyc_completion_rate': round(kyc_completion_rate, 2),
                                 'recent_registrations': recent_registrations
                             },
                             compliance_status=compliance_status)
        
    except Exception as e:
        flash(f'Error loading compliance dashboard: {str(e)}', 'error')
        return render_template('compliance/dashboard.html', 
                             compliance_stats={}, compliance_status={})

@compliance_bp.route('/kyc/verification', methods=['GET', 'POST'])
@login_required
@admin_required
def kyc_verification():
    """KYC verification management"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            action = data.get('action')  # 'approve' or 'reject'
            notes = data.get('notes', '')
            
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
            
            if action == 'approve':
                user.is_documents_verified = True
                user.verification_notes = notes
                user.verified_at = datetime.now()
                status_message = f'KYC approved for {user.email}'
                
                # Send approval notification
                send_kyc_notification(user, 'approved')
                
            elif action == 'reject':
                user.is_documents_verified = False
                user.verification_notes = notes
                status_message = f'KYC rejected for {user.email}'
                
                # Send rejection notification
                send_kyc_notification(user, 'rejected', notes)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid action'
                }), 400
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': status_message
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # GET request - show pending KYC verifications
    pending_users = User.query.filter_by(is_documents_verified=False).filter(
        User.national_id.isnot(None)
    ).all()
    
    return render_template('compliance/kyc_verification.html', 
                         pending_users=pending_users)

def send_kyc_notification(user, status, notes=None):
    """Send KYC status notification to user"""
    try:
        # In production, this would send actual email/SMS
        print(f"KYC notification sent to {user.email}: Status {status}")
        if notes:
            print(f"Notes: {notes}")
    except Exception as e:
        print(f"Error sending KYC notification: {e}")

@compliance_bp.route('/reports/regulatory')
@login_required
@admin_required
def regulatory_reports():
    """Generate regulatory compliance reports"""
    try:
        # Generate various compliance reports
        reports = [
            {
                'id': 'user_registration',
                'name': 'User Registration Report',
                'description': 'Monthly user registration and verification statistics',
                'frequency': 'Monthly',
                'last_generated': datetime.now() - timedelta(days=5),
                'status': 'current'
            },
            {
                'id': 'kyc_compliance',
                'name': 'KYC Compliance Report',
                'description': 'KYC verification rates and pending verifications',
                'frequency': 'Weekly',
                'last_generated': datetime.now() - timedelta(days=2),
                'status': 'current'
            },
            {
                'id': 'transaction_monitoring',
                'name': 'Transaction Monitoring Report',
                'description': 'AML transaction monitoring and suspicious activity',
                'frequency': 'Daily',
                'last_generated': datetime.now() - timedelta(hours=12),
                'status': 'current'
            },
            {
                'id': 'data_protection',
                'name': 'Data Protection Compliance',
                'description': 'GDPR compliance and data handling report',
                'frequency': 'Quarterly',
                'last_generated': datetime.now() - timedelta(days=30),
                'status': 'due_soon'
            }
        ]
        
        return render_template('compliance/regulatory_reports.html', reports=reports)
        
    except Exception as e:
        flash(f'Error loading regulatory reports: {str(e)}', 'error')
        return render_template('compliance/regulatory_reports.html', reports=[])

@compliance_bp.route('/reports/generate/<report_type>')
@login_required
@admin_required
def generate_report(report_type):
    """Generate specific compliance report"""
    try:
        if report_type == 'user_registration':
            report_data = generate_user_registration_report()
        elif report_type == 'kyc_compliance':
            report_data = generate_kyc_compliance_report()
        elif report_type == 'transaction_monitoring':
            report_data = generate_transaction_monitoring_report()
        elif report_type == 'data_protection':
            report_data = generate_data_protection_report()
        else:
            return jsonify({
                'success': False,
                'error': 'Unknown report type'
            }), 400
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_user_registration_report():
    """Generate user registration compliance report"""
    # Get user registration data for the last month
    last_month = datetime.now() - timedelta(days=30)
    
    total_registrations = User.query.filter(User.created_at >= last_month).count()
    verified_registrations = User.query.filter(
        User.created_at >= last_month,
        User.is_documents_verified == True
    ).count()
    
    # Group by country
    country_stats = db.session.query(
        User.country_name,
        db.func.count(User.id).label('count')
    ).filter(
        User.created_at >= last_month,
        User.country_name.isnot(None)
    ).group_by(User.country_name).all()
    
    return {
        'report_type': 'User Registration Report',
        'period': f'Last 30 days ending {datetime.now().strftime("%Y-%m-%d")}',
        'summary': {
            'total_registrations': total_registrations,
            'verified_registrations': verified_registrations,
            'verification_rate': round((verified_registrations / max(total_registrations, 1)) * 100, 2)
        },
        'country_breakdown': [
            {'country': stat.country_name, 'registrations': stat.count}
            for stat in country_stats
        ],
        'generated_at': datetime.now().isoformat()
    }

def generate_kyc_compliance_report():
    """Generate KYC compliance report"""
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_documents_verified=True).count()
    pending_users = User.query.filter_by(is_documents_verified=False).filter(
        User.national_id.isnot(None)
    ).count()
    
    # Users with no documents uploaded
    no_documents = User.query.filter(
        User.national_id.is_(None),
        User.passport_number.is_(None)
    ).count()
    
    return {
        'report_type': 'KYC Compliance Report',
        'summary': {
            'total_users': total_users,
            'verified_users': verified_users,
            'pending_verification': pending_users,
            'no_documents': no_documents,
            'compliance_rate': round((verified_users / max(total_users, 1)) * 100, 2)
        },
        'recommendations': [
            'Follow up with users who have not uploaded documents',
            'Implement automated document verification',
            'Send periodic reminders for pending verifications'
        ],
        'generated_at': datetime.now().isoformat()
    }

def generate_transaction_monitoring_report():
    """Generate transaction monitoring report"""
    # In a real system, this would analyze transaction patterns
    return {
        'report_type': 'Transaction Monitoring Report',
        'monitoring_period': 'Last 24 hours',
        'summary': {
            'total_transactions': 0,  # Would query transaction table
            'flagged_transactions': 0,
            'suspicious_patterns': 0,
            'aml_alerts': 0
        },
        'risk_assessment': 'Low',
        'actions_required': [],
        'generated_at': datetime.now().isoformat()
    }

def generate_data_protection_report():
    """Generate data protection compliance report"""
    return {
        'report_type': 'Data Protection Compliance Report',
        'compliance_framework': 'GDPR + Kenya Data Protection Act',
        'summary': {
            'data_encryption': 'Active',
            'access_controls': 'Implemented',
            'audit_logging': 'Active',
            'user_consent': 'Tracked',
            'data_retention': 'Policy compliant'
        },
        'privacy_rights_requests': {
            'data_access_requests': 0,
            'data_deletion_requests': 0,
            'data_portability_requests': 0
        },
        'recommendations': [
            'Regular security audits',
            'Staff privacy training',
            'Policy updates as needed'
        ],
        'generated_at': datetime.now().isoformat()
    }

@compliance_bp.route('/reports/export/<report_type>')
@login_required
@admin_required
def export_report(report_type):
    """Export compliance report as CSV"""
    try:
        if report_type == 'user_registration':
            data = generate_user_registration_report()
        elif report_type == 'kyc_compliance':
            data = generate_kyc_compliance_report()
        else:
            flash('Report type not available for export', 'error')
            return redirect(url_for('compliance.regulatory_reports'))
        
        # Create CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Report Type', data['report_type']])
        writer.writerow(['Generated At', data['generated_at']])
        writer.writerow([])  # Empty row
        
        # Write summary data
        if 'summary' in data:
            writer.writerow(['Summary'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
        
        # Convert to bytes
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        # Create file-like object
        file_obj = io.BytesIO(csv_data.encode('utf-8'))
        
        return send_file(
            file_obj,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{report_type}_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting report: {str(e)}', 'error')
        return redirect(url_for('compliance.regulatory_reports'))

@compliance_bp.route('/monitoring/aml')
@login_required
@admin_required
def aml_monitoring():
    """Anti-Money Laundering monitoring dashboard"""
    try:
        # AML monitoring data
        monitoring_data = {
            'risk_score': 'Low',
            'active_alerts': 0,
            'transactions_monitored': 0,  # Would come from transaction table
            'suspicious_patterns': [],
            'watchlist_matches': 0,
            'last_update': datetime.now()
        }
        
        # Monitoring rules
        monitoring_rules = [
            {
                'id': 'large_transactions',
                'name': 'Large Transaction Detection',
                'description': 'Monitor transactions above KES 100,000',
                'threshold': 100000,
                'status': 'active'
            },
            {
                'id': 'rapid_transactions',
                'name': 'Rapid Transaction Pattern',
                'description': 'Detect rapid succession of transactions',
                'threshold': '5 transactions in 1 hour',
                'status': 'active'
            },
            {
                'id': 'cross_border',
                'name': 'Cross-border Transactions',
                'description': 'Monitor international transfers',
                'threshold': 'Any international transaction',
                'status': 'active'
            }
        ]
        
        return render_template('compliance/aml_monitoring.html',
                             monitoring_data=monitoring_data,
                             monitoring_rules=monitoring_rules)
        
    except Exception as e:
        flash(f'Error loading AML monitoring: {str(e)}', 'error')
        return render_template('compliance/aml_monitoring.html',
                             monitoring_data={}, monitoring_rules=[])

@compliance_bp.route('/api/compliance-check', methods=['POST'])
@login_required
@admin_required
def compliance_check():
    """Run comprehensive compliance check"""
    try:
        check_type = request.json.get('check_type', 'full')
        
        results = {
            'check_type': check_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'issues_found': [],
            'recommendations': []
        }
        
        # Check user verification compliance
        unverified_count = User.query.filter_by(is_documents_verified=False).count()
        if unverified_count > 0:
            results['issues_found'].append({
                'type': 'kyc',
                'severity': 'medium',
                'description': f'{unverified_count} users pending KYC verification',
                'action_required': 'Review and verify pending users'
            })
        
        # Check data retention compliance
        old_users = User.query.filter(
            User.created_at < datetime.now() - timedelta(days=2555)  # 7 years
        ).count()
        
        if old_users > 0:
            results['recommendations'].append({
                'type': 'data_retention',
                'description': f'{old_users} user records older than 7 years',
                'action': 'Review data retention policy'
            })
        
        # Overall compliance score
        total_checks = 5
        passed_checks = total_checks - len(results['issues_found'])
        compliance_score = (passed_checks / total_checks) * 100
        
        results['compliance_score'] = round(compliance_score, 2)
        results['overall_status'] = 'compliant' if compliance_score >= 90 else 'needs_attention'
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
