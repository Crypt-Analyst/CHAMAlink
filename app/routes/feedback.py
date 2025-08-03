"""
Feedback routes for CHAMAlink
Handles user feedback collection and management
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime
import json
import os

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/submit', methods=['POST'])
def submit_feedback():
    """Handle feedback submission"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('rating') or not data.get('message'):
            return jsonify({
                'success': False,
                'message': 'Rating and message are required'
            }), 400
        
        # Create feedback record
        feedback_data = {
            'id': f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id if current_user.is_authenticated else 'anonymous'}",
            'user_id': current_user.id if current_user.is_authenticated else None,
            'user_email': current_user.email if current_user.is_authenticated else data.get('email'),
            'rating': int(data.get('rating')),
            'message': data.get('message', '').strip(),
            'email': data.get('email'),
            'allow_contact': data.get('allow_contact', False),
            'page_url': data.get('page_url'),
            'user_agent': data.get('user_agent'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'created_at': datetime.now().isoformat(),
            'status': 'new'
        }
        
        # Store feedback (for now, save to file - in production, save to database)
        feedback_file = 'feedback_submissions.json'
        feedback_list = []
        
        # Load existing feedback
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedback_list = json.load(f)
            except:
                feedback_list = []
        
        # Add new feedback
        feedback_list.append(feedback_data)
        
        # Save feedback
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_list, f, indent=2, ensure_ascii=False)

        # Send feedback to system email
        try:
            from flask_mail import Message
            from flask import current_app
            from app import mail
            msg = Message(
                subject=f"New Feedback: {feedback_data['rating']}/5 from {feedback_data.get('user_email', 'anonymous')}",
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@chamalink.com'),
                recipients=['rahasoft.app@gmail.com'],
                body=f"""
New Feedback Submitted:
Rating: {feedback_data['rating']}/5
Message: {feedback_data['message']}
User Email: {feedback_data.get('user_email', 'anonymous')}
Allow Contact: {feedback_data.get('allow_contact', False)}
Page URL: {feedback_data.get('page_url', '')}
User Agent: {feedback_data.get('user_agent', '')}
Timestamp: {feedback_data.get('timestamp', '')}
        """
            )
            mail.send(msg)
        except Exception as mail_err:
            print(f"❌ Error sending feedback email: {mail_err}")
        
        # Log feedback submission
        print(f"📝 New feedback submitted: Rating {feedback_data['rating']}/5 from {feedback_data.get('user_email', 'anonymous')}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback_data['id']
        })
        
    except Exception as e:
        print(f"❌ Error submitting feedback: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@feedback_bp.route('/admin')
def admin_feedback():
    """Admin page to view feedback (basic implementation)"""
    try:
        # Load feedback data
        feedback_file = 'feedback_submissions.json'
        feedback_list = []
        
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_list = json.load(f)
        
        # Sort by timestamp (newest first)
        feedback_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return render_template('admin/feedback.html', feedback_list=feedback_list)
        
    except Exception as e:
        flash(f'Error loading feedback: {e}', 'error')
        return redirect(url_for('main.home'))

@feedback_bp.route('/test')
def test_feedback():
    """Test page for feedback functionality"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Feedback Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>Feedback Test Page</h2>
            <button class="btn btn-primary" onclick="testFeedback()">Test Feedback Submission</button>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                function testFeedback() {
                    fetch('/feedback/submit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            rating: 5,
                            message: 'Test feedback submission',
                            email: 'test@example.com',
                            allow_contact: true,
                            page_url: window.location.href,
                            user_agent: navigator.userAgent,
                            timestamp: new Date().toISOString()
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Feedback result: ' + JSON.stringify(data));
                    })
                    .catch(error => {
                        alert('Error: ' + error);
                    });
                }
            </script>
        </div>
    </body>
    </html>
    '''
