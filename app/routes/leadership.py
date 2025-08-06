"""
Leadership Management Routes
==========================
Handles leadership roles assignment and elections
"""
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.chama import Chama, chama_members, LeadershipElection, ElectionVote
from app.models.user import User
from app.models.notification import Notification
from app.utils.permissions import user_can_admin_chama
from app import db
from datetime import datetime, timedelta
import json

leadership_bp = Blueprint('leadership', __name__, url_prefix='/leadership')

@leadership_bp.route('/chama/<int:chama_id>/manage')
@login_required
def manage_leadership(chama_id):
    """Manage chama leadership roles"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions - only admin/creator can access
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator']:
        flash('Access denied. Only admins can manage leadership.', 'error')
        return redirect(url_for('chama.chama_detail', chama_id=chama_id))
    
    # Get current leadership
    current_leadership = chama.get_leadership()
    
    # Get all members who can be leaders
    eligible_members = chama.members
    
    # Check if there are any active elections
    active_elections = LeadershipElection.query.filter_by(
        chama_id=chama_id, status='active'
    ).all()
    
    return render_template('leadership/manage.html',
                         chama=chama,
                         current_leadership=current_leadership,
                         eligible_members=eligible_members,
                         active_elections=active_elections,
                         user_role=user_role)

@leadership_bp.route('/chama/<int:chama_id>/assign-role', methods=['POST'])
@login_required
def assign_role(chama_id):
    """Assign leadership role (Creator only, before elections)"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions - only creator can directly assign roles
    user_role = current_user.get_chama_role(chama_id)
    if user_role != 'creator':
        return jsonify({'success': False, 'message': 'Only the creator can assign roles directly'}), 403
    
    try:
        user_id = request.json.get('user_id')
        role = request.json.get('role')
        
        if not user_id or not role:
            return jsonify({'success': False, 'message': 'User ID and role are required'}), 400
        
        if role not in ['chairperson', 'secretary', 'treasurer']:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        # Check if user is a member
        member = User.query.join(chama_members).filter(
            chama_members.c.user_id == user_id,
            chama_members.c.chama_id == chama_id
        ).first()
        
        if not member:
            return jsonify({'success': False, 'message': 'User is not a member of this chama'}), 400
        
        # Update member role
        db.session.execute(
            chama_members.update().where(
                (chama_members.c.user_id == user_id) & 
                (chama_members.c.chama_id == chama_id)
            ).values(
                role=role,
                elected_at=datetime.utcnow()
            )
        )
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            type='role_assigned',
            title='Leadership Role Assigned',
            message=f'You have been appointed as {role.title()} of {chama.name}.',
            chama_id=chama_id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Role {role} assigned successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@leadership_bp.route('/chama/<int:chama_id>/start-election', methods=['POST'])
@login_required
def start_election(chama_id):
    """Start leadership election"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check permissions
    user_role = current_user.get_chama_role(chama_id)
    if user_role not in ['admin', 'creator']:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        position = request.json.get('position')
        duration_days = request.json.get('duration_days', 7)  # Default 7 days
        
        if position not in ['chairperson', 'secretary', 'treasurer']:
            return jsonify({'success': False, 'message': 'Invalid position'}), 400
        
        # Check if there's already an active election for this position
        existing_election = LeadershipElection.query.filter_by(
            chama_id=chama_id,
            position=position,
            status='active'
        ).first()
        
        if existing_election:
            return jsonify({'success': False, 'message': 'There is already an active election for this position'}), 400
        
        # Create election
        election = LeadershipElection(
            chama_id=chama_id,
            position=position,
            initiated_by=current_user.id,
            election_end_date=datetime.utcnow() + timedelta(days=duration_days),
            status='active'
        )
        db.session.add(election)
        db.session.flush()
        
        # Notify all members
        for member in chama.members:
            notification = Notification(
                user_id=member.id,
                type='election_started',
                title='Leadership Election Started',
                message=f'Election for {position.title()} position has started in {chama.name}. Cast your vote!',
                chama_id=chama_id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Election for {position} started successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@leadership_bp.route('/chama/<int:chama_id>/elections')
@login_required
def view_elections(chama_id):
    """View active elections"""
    chama = Chama.query.get_or_404(chama_id)
    
    # Check if user is a member
    user_role = current_user.get_chama_role(chama_id)
    if not user_role:
        flash('You must be a member to view elections.', 'error')
        return redirect(url_for('chama.chama_detail', chama_id=chama_id))
    
    # Get active elections
    active_elections = LeadershipElection.query.filter_by(
        chama_id=chama_id, status='active'
    ).all()
    
    # Get user's votes
    user_votes = {}
    for election in active_elections:
        vote = ElectionVote.query.filter_by(
            election_id=election.id,
            voter_id=current_user.id
        ).first()
        if vote:
            user_votes[election.id] = vote.candidate_id
    
    return render_template('leadership/elections.html',
                         chama=chama,
                         active_elections=active_elections,
                         user_votes=user_votes,
                         user_role=user_role)

@leadership_bp.route('/election/<int:election_id>/vote', methods=['POST'])
@login_required
def cast_vote(election_id):
    """Cast vote in leadership election"""
    election = LeadershipElection.query.get_or_404(election_id)
    
    # Check if user is a member
    user_role = current_user.get_chama_role(election.chama_id)
    if not user_role:
        return jsonify({'success': False, 'message': 'You must be a member to vote'}), 403
    
    # Check if election is still active
    if election.status != 'active' or election.election_end_date < datetime.utcnow():
        return jsonify({'success': False, 'message': 'This election is no longer active'}), 400
    
    try:
        candidate_id = request.json.get('candidate_id')
        
        if not candidate_id:
            return jsonify({'success': False, 'message': 'Candidate ID is required'}), 400
        
        # Check if candidate is a valid member
        candidate = User.query.join(chama_members).filter(
            chama_members.c.user_id == candidate_id,
            chama_members.c.chama_id == election.chama_id
        ).first()
        
        if not candidate:
            return jsonify({'success': False, 'message': 'Invalid candidate'}), 400
        
        # Check if user has already voted
        existing_vote = ElectionVote.query.filter_by(
            election_id=election_id,
            voter_id=current_user.id
        ).first()
        
        if existing_vote:
            # Update existing vote
            existing_vote.candidate_id = candidate_id
            existing_vote.voted_at = datetime.utcnow()
        else:
            # Create new vote
            vote = ElectionVote(
                election_id=election_id,
                voter_id=current_user.id,
                candidate_id=candidate_id
            )
            db.session.add(vote)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Vote cast successfully!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@leadership_bp.route('/election/<int:election_id>/results')
@login_required
def election_results(election_id):
    """View election results"""
    election = LeadershipElection.query.get_or_404(election_id)
    
    # Check if user is a member
    user_role = current_user.get_chama_role(election.chama_id)
    if not user_role:
        flash('You must be a member to view results.', 'error')
        return redirect(url_for('chama.chama_detail', chama_id=election.chama_id))
    
    # Get vote counts
    votes = db.session.query(
        ElectionVote.candidate_id,
        db.func.count(ElectionVote.id).label('vote_count')
    ).filter_by(election_id=election_id).group_by(ElectionVote.candidate_id).all()
    
    # Get candidate details
    results = []
    for candidate_id, vote_count in votes:
        candidate = User.query.get(candidate_id)
        results.append({
            'candidate': candidate,
            'vote_count': vote_count
        })
    
    # Sort by vote count
    results.sort(key=lambda x: x['vote_count'], reverse=True)
    
    return render_template('leadership/results.html',
                         election=election,
                         results=results,
                         user_role=user_role)
