"""
SMS service for sending 2FA codes and notifications
"""
import requests
import os
from flask import current_app

class SMSService:
    def __init__(self):
        # Initialize Africa's Talking
        username = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
        api_key = os.getenv('AFRICASTALKING_API_KEY')
        
        if api_key:
            try:
                import africastalking
                africastalking.initialize(username, api_key)
                self.sms = africastalking.SMS
            except ImportError:
                # Only log if we're in an application context
                try:
                    from flask import current_app
                    current_app.logger.warning("Africa's Talking package not found. SMS service disabled.")
                except RuntimeError:
                    # We're outside application context, which is fine during import
                    pass
                self.sms = None
        else:
            # Only log if we're in an application context
            try:
                from flask import current_app
                current_app.logger.warning("Africa's Talking API key not found. SMS service disabled.")
            except RuntimeError:
                # We're outside application context, which is fine during import
                pass
            self.sms = None
    
    def send_sms(self, phone_number, message):
        """Send SMS to a phone number"""
        if not self.sms:
            try:
                from flask import current_app
                current_app.logger.warning("SMS service not configured")
            except RuntimeError:
                pass
            return False, "SMS service not configured"
        
        try:
            # Format phone number (ensure it starts with +254)
            if phone_number.startswith('0'):
                phone_number = '+254' + phone_number[1:]
            elif not phone_number.startswith('+'):
                phone_number = '+254' + phone_number
            
            # Send SMS
            response = self.sms.send(message, [phone_number])
            
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                if recipient['status'] == 'Success':
                    return True, f"SMS sent successfully to {phone_number}"
                else:
                    return False, f"Failed to send SMS: {recipient['status']}"
            else:
                return False, "No recipients found"
                
        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.error(f"SMS sending error: {str(e)}")
            except RuntimeError:
                pass
            return False, f"SMS sending error: {str(e)}"
    
    def send_bulk_sms(self, phone_numbers, message):
        """Send SMS to multiple phone numbers"""
        if not self.sms:
            return False, "SMS service not configured"
        
        try:
            # Format all phone numbers
            formatted_numbers = []
            for phone in phone_numbers:
                if phone.startswith('0'):
                    formatted_numbers.append('+254' + phone[1:])
                elif not phone.startswith('+'):
                    formatted_numbers.append('+254' + phone)
                else:
                    formatted_numbers.append(phone)
            
            # Send bulk SMS
            response = self.sms.send(message, formatted_numbers)
            
            successful = 0
            failed = 0
            
            if response['SMSMessageData']['Recipients']:
                for recipient in response['SMSMessageData']['Recipients']:
                    if recipient['status'] == 'Success':
                        successful += 1
                    else:
                        failed += 1
            
            return True, f"SMS sent: {successful} successful, {failed} failed"
            
        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.error(f"Bulk SMS sending error: {str(e)}")
            except RuntimeError:
                pass
            return False, f"Bulk SMS sending error: {str(e)}"

# Global SMS service instance
sms_service = SMSService()

def send_2fa_code_sms(phone_number, code):
    """Send 2FA code via SMS"""
    message = f"Your ChamaLink verification code is: {code}. This code expires in 10 minutes."
    return sms_service.send_sms(phone_number, message)

def send_loan_approval_sms(user, chama, loan_amount):
    """Send SMS notification when loan is approved"""
    message = f"""
Dear {user.first_name},
Your loan of KES {loan_amount:,.2f} from {chama.name} has been approved! 
Funds will be disbursed to your M-Pesa shortly.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_penalty_assignment_sms(user, chama, penalty_type, amount):
    """Send SMS notification when penalty is assigned"""
    message = f"""
Dear {user.first_name},
A penalty of KES {amount:,.2f} for {penalty_type} has been assigned to you in {chama.name}.
Please log in to ChamaLink to view details and make payment.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_meeting_reminder_sms(user, chama, meeting_date):
    """Send SMS reminder for upcoming meeting"""
    message = f"""
Dear {user.first_name},
Reminder: {chama.name} meeting scheduled for {meeting_date.strftime('%A, %B %d, %Y')}.
Don't forget to attend!
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_contribution_reminder_sms(user, chama, amount_due):
    """Send SMS reminder for contribution due"""
    message = f"""
Dear {user.first_name},
Your contribution of KES {amount_due:,.2f} to {chama.name} is due.
Please make your payment via M-Pesa or log in to ChamaLink.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_payment_confirmation_sms(user, chama, amount, transaction_id):
    """Send SMS confirmation when payment is received"""
    message = f"""
Dear {user.first_name},
Payment confirmed! KES {amount:,.2f} received for {chama.name}.
Transaction ID: {transaction_id}
Thank you for your contribution.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_membership_approved_sms(user, chama):
    """Send SMS when membership is approved"""
    message = f"""
Dear {user.first_name},
Congratulations! Your membership to {chama.name} has been approved.
Log in to ChamaLink to complete your registration fee payment and start participating.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_loan_disbursement_sms(user, chama, amount, mpesa_number):
    """Send SMS when loan is disbursed"""
    message = f"""
Dear {user.first_name},
Your loan of KES {amount:,.2f} from {chama.name} has been disbursed to {mpesa_number}.
Please check your M-Pesa messages for confirmation.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(user.phone, message)

def send_bulk_meeting_reminder(chama, meeting_date):
    """Send meeting reminder to all chama members"""
    from app.models.user import User
    from app.models.chama import chama_members
    from app import db
    
    # Get all members of the chama
    members = db.session.query(User).join(chama_members).filter(
        chama_members.c.chama_id == chama.id
    ).all()
    
    phone_numbers = [member.phone for member in members if member.phone]
    
    if not phone_numbers:
        return False, "No phone numbers found for members"
    
    message = f"""
Dear Members,
Reminder: {chama.name} meeting scheduled for {meeting_date.strftime('%A, %B %d, %Y')}.
Venue: [Meeting Location]
Time: [Meeting Time]
Agenda: [Meeting Agenda]
Please attend on time.
- {chama.name} Management
""".strip()
    
    return sms_service.send_bulk_sms(phone_numbers, message)

def send_chama_creation_sms(creator, chama):
    """Send SMS when a new chama is created"""
    message = f"""
Dear {creator.first_name},
Congratulations! Your chama '{chama.name}' has been successfully created on ChamaLink.
You can now invite members and start managing your group finances digitally.
- ChamaLink Team
""".strip()
    
    return sms_service.send_sms(creator.phone, message)

def send_member_invitation_sms(invitee_phone, inviter_name, chama_name, join_link):
    """Send SMS invitation to join a chama"""
    message = f"""
Dear Member,
{inviter_name} has invited you to join '{chama_name}' on ChamaLink - Kenya's leading chama management platform.
Join here: {join_link}
- ChamaLink
""".strip()
    
    return sms_service.send_sms(invitee_phone, message)

def send_loan_application_sms(admins, applicant, chama, loan_amount):
    """Send SMS to admins when new loan application is submitted"""
    admin_phones = [admin.phone for admin in admins if admin.phone]
    
    if not admin_phones:
        return False, "No admin phone numbers found"
    
    message = f"""
New Loan Alert - {chama.name}
{applicant.first_name} {applicant.last_name} has applied for a loan of KES {loan_amount:,.2f}.
Please log in to ChamaLink to review and approve.
- ChamaLink
""".strip()
    
    return sms_service.send_bulk_sms(admin_phones, message)

def send_loan_repayment_reminder_sms(borrower, chama, amount_due, due_date):
    """Send SMS reminder for loan repayment"""
    message = f"""
Payment Reminder - {chama.name}
Dear {borrower.first_name},
Your loan repayment of KES {amount_due:,.2f} is due on {due_date.strftime('%B %d, %Y')}.
Please make payment via M-Pesa or contact your chama treasurer.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(borrower.phone, message)

def send_savings_goal_achievement_sms(members, chama, goal_name, amount_achieved):
    """Send SMS when chama achieves a savings goal"""
    member_phones = [member.phone for member in members if member.phone]
    
    if not member_phones:
        return False, "No member phone numbers found"
    
    message = f"""
🎉 Goal Achieved! - {chama.name}
Congratulations! We've reached our savings goal '{goal_name}' with KES {amount_achieved:,.2f}!
Thank you for your commitment and contributions.
- ChamaLink
""".strip()
    
    return sms_service.send_bulk_sms(member_phones, message)

def send_emergency_alert_sms(members, chama, alert_message, sender_name):
    """Send emergency alert to all chama members"""
    member_phones = [member.phone for member in members if member.phone]
    
    if not member_phones:
        return False, "No member phone numbers found"
    
    message = f"""
🚨 URGENT - {chama.name}
From: {sender_name}
{alert_message}
Please respond or contact your chama officials immediately.
- ChamaLink Emergency Alert
""".strip()
    
    return sms_service.send_bulk_sms(member_phones, message)

def send_monthly_statement_sms(member, chama, total_contributions, total_loans, balance):
    """Send monthly financial statement summary"""
    message = f"""
Monthly Statement - {chama.name}
Dear {member.first_name},
This month:
• Contributions: KES {total_contributions:,.2f}
• Loans taken: KES {total_loans:,.2f}  
• Account balance: KES {balance:,.2f}
Full statement available on ChamaLink.
- ChamaLink
""".strip()
    
    return sms_service.send_sms(member.phone, message)

def send_agm_reminder_sms(members, chama, agm_date, venue):
    """Send AGM (Annual General Meeting) reminder"""
    member_phones = [member.phone for member in members if member.phone]
    
    if not member_phones:
        return False, "No member phone numbers found"
    
    message = f"""
AGM Reminder - {chama.name}
Dear Members,
Annual General Meeting scheduled for {agm_date.strftime('%A, %B %d, %Y')}.
Venue: {venue}
Attendance is mandatory. Please confirm your participation.
- {chama.name} Management
""".strip()
    
    return sms_service.send_bulk_sms(member_phones, message)

def send_late_payment_warning_sms(member, chama, overdue_amount, penalty_amount):
    """Send warning for late payments"""
    message = f"""
Payment Overdue - {chama.name}
Dear {member.first_name},
You have an overdue payment of KES {overdue_amount:,.2f}.
Late penalty: KES {penalty_amount:,.2f}
Please settle immediately to avoid additional charges.
- {chama.name} Treasury
""".strip()
    
    return sms_service.send_sms(member.phone, message)

def send_welcome_new_member_sms(new_member, chama, treasurer_contact):
    """Send welcome message to new chama member"""
    message = f"""
Welcome to {chama.name}! 🎉
Dear {new_member.first_name},
You're now a registered member. Your journey to financial empowerment starts here!
Treasurer contact: {treasurer_contact}
Access your account: chamalink.co.ke
- ChamaLink & {chama.name}
""".strip()
    
    return sms_service.send_sms(new_member.phone, message)

def send_system_maintenance_sms(users, maintenance_date, duration):
    """Send system maintenance notification"""
    user_phones = [user.phone for user in users if user.phone]
    
    if not user_phones:
        return False, "No user phone numbers found"
    
    message = f"""
System Maintenance Notice
ChamaLink will be under maintenance on {maintenance_date.strftime('%B %d, %Y')} for {duration}.
Services will be temporarily unavailable. We apologize for any inconvenience.
- ChamaLink Technical Team
""".strip()
    
    return sms_service.send_bulk_sms(user_phones, message)

def send_suspicious_activity_alert_sms(admins, chama, activity_description):
    """Send alert for suspicious account activity"""
    admin_phones = [admin.phone for admin in admins if admin.phone]
    
    if not admin_phones:
        return False, "No admin phone numbers found"
    
    message = f"""
🔒 Security Alert - {chama.name}
Suspicious activity detected: {activity_description}
Please log in to ChamaLink immediately to review and secure your account.
- ChamaLink Security Team
""".strip()
    
    return sms_service.send_bulk_sms(admin_phones, message)
