from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Chama, User, chama_members
from app.models.chama import LeadershipElection, ElectionCandidate, ElectionVote
from app.utils.permissions import chama_member_required, get_user_chama_role
from app import db
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_, func

elections_bp = Blueprint('elections', __name__, url_prefix='/elections')

@elections_bp.route('/chama/<int:chama_id>')
@login_required
@chama_member_required
def chama_elections(chama_id):
    """View all elections for a chama"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        user_role = get_user_chama_role(current_user.id, chama_id)
        
        # Get all elections for this chama
        elections = LeadershipElection.query.filter_by(chama_id=chama_id).order_by(desc(LeadershipElection.created_at)).all()
        
        # Get current leadership
        leadership = chama.leadership
        
        return render_template('elections/chama_elections.html',
                             chama=chama,
                             elections=elections,
                             leadership=leadership,
                             user_role=user_role)
                             
    except Exception as e:
        current_app.logger.error(f"Error loading chama elections: {e}")
        flash('Error loading elections', 'error')
        return redirect(url_for('chama.chama_dashboard', chama_id=chama_id))

@elections_bp.route('/create/<int:chama_id>', methods=['GET', 'POST'])
@login_required
@chama_member_required
def create_election(chama_id):
    """Create a new leadership election"""
    try:
        chama = Chama.query.get_or_404(chama_id)
        
        # Check if user can create elections
        if not chama.can_user_access_feature(current_user.id, 'create_elections'):
            flash('You do not have permission to create elections', 'error')
            return redirect(url_for('elections.chama_elections', chama_id=chama_id))
        
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            
            # Validate required fields
            required_fields = ['position', 'title', 'nomination_days', 'voting_days']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'{field.replace("_", " ").title()} is required'})
            
            position = data.get('position')
            if position not in ['chairperson', 'secretary', 'treasurer']:
                return jsonify({'success': False, 'message': 'Invalid position'})
            
            # Check if there's already an active election for this position
            existing_election = LeadershipElection.query.filter(
                LeadershipElection.chama_id == chama_id,
                LeadershipElection.position == position,
                LeadershipElection.status.in_(['upcoming', 'nominations', 'voting'])
            ).first()
            
            if existing_election:
                return jsonify({'success': False, 'message': f'There is already an active election for {position}'})
            
            # Calculate dates
            now = datetime.utcnow()
            nomination_start = now + timedelta(hours=1)  # Start nominations in 1 hour
            nomination_end = nomination_start + timedelta(days=int(data.get('nomination_days', 3)))
            voting_start = nomination_end + timedelta(hours=1)
            voting_end = voting_start + timedelta(days=int(data.get('voting_days', 3)))
            
            # Create election
            election = LeadershipElection(
                chama_id=chama_id,
                position=position,
                title=data.get('title'),
                description=data.get('description', ''),
                nomination_start=nomination_start,
                nomination_end=nomination_end,
                voting_start=voting_start,
                voting_end=voting_end,
                created_by=current_user.id,
                status='upcoming'
            )
            
            db.session.add(election)
            db.session.commit()
            
            # Notify all members
            from app.models.notification import Notification
            members = db.session.query(chama_members.c.user_id).filter(
                chama_members.c.chama_id == chama_id
            ).all()
            
            for member_id_tuple in members:
                member_id = member_id_tuple[0]
                notification = Notification(
                    user_id=member_id,
                    chama_id=chama_id,
                    title=f'New Election: {position.title()}',
                    message=f'A new election for {position.title()} has been created in {chama.name}. Nominations start soon!',
                    type='election_created',
                    related_id=election.id
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Election created successfully!',
                'election_id': election.id
            })
        
        return render_template('elections/create_election.html', chama=chama)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating election: {e}")
        return jsonify({'success': False, 'message': str(e)})

@elections_bp.route('/<int:election_id>')
@login_required
def election_detail(election_id):
    """View election details"""
    try:
        election = LeadershipElection.query.get_or_404(election_id)
        chama = election.chama
        
        # Check if user is a member
        user_role = get_user_chama_role(current_user.id, chama.id)
        if not user_role:
            flash('You must be a member to view this election', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Get candidates and results
        candidates = election.get_candidates()
        current_phase = election.current_phase
        
        # Check if user has voted
        user_vote = None
        if current_phase == 'voting' or current_phase == 'completed':
            user_vote = ElectionVote.query.filter_by(
                election_id=election_id,
                voter_id=current_user.id
            ).first()
        
        # Get results if election is completed or user has voted
        results = []
        if current_phase == 'completed' or user_vote:
            results = election.get_results()
        
        return render_template('elections/election_detail.html',
                             election=election,
                             chama=chama,
                             candidates=candidates,
                             current_phase=current_phase,
                             user_vote=user_vote,
                             results=results,
                             user_role=user_role)
                             
    except Exception as e:
        current_app.logger.error(f"Error loading election details: {e}")
        flash('Error loading election details', 'error')
        return redirect(url_for('main.dashboard'))

@elections_bp.route('/<int:election_id>/nominate', methods=['POST'])
@login_required
def nominate_candidate(election_id):
    """Nominate a candidate for election"""
    try:
        election = LeadershipElection.query.get_or_404(election_id)
        
        # Check if nominations are open
        if election.current_phase != 'nominations':
            return jsonify({'success': False, 'message': 'Nominations are not currently open'})
        
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        manifesto = data.get('manifesto', '')
        
        if not candidate_id:
            return jsonify({'success': False, 'message': 'Candidate is required'})
        
        # Check if candidate is a chama member
        candidate_role = get_user_chama_role(candidate_id, election.chama_id)
        if not candidate_role:
            return jsonify({'success': False, 'message': 'Candidate must be a chama member'})
        
        # Check if already nominated
        existing_nomination = ElectionCandidate.query.filter_by(
            election_id=election_id,
            candidate_id=candidate_id
        ).first()
        
        if existing_nomination:
            return jsonify({'success': False, 'message': 'This person is already nominated'})
        
        # Create nomination
        nomination = ElectionCandidate(
            election_id=election_id,
            candidate_id=candidate_id,
            manifesto=manifesto,
            nominated_by=current_user.id
        )
        
        db.session.add(nomination)
        db.session.commit()
        
        # Notify the candidate
        from app.models.notification import Notification
        notification = Notification(
            user_id=candidate_id,
            chama_id=election.chama_id,
            title='You have been nominated!',
            message=f'You have been nominated for {election.position.title()} in {election.chama.name}',
            type='nomination_received',
            related_id=election.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Candidate nominated successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error nominating candidate: {e}")
        return jsonify({'success': False, 'message': str(e)})

@elections_bp.route('/<int:election_id>/vote', methods=['POST'])
@login_required
def cast_vote(election_id):
    """Cast vote in election"""
    try:
        election = LeadershipElection.query.get_or_404(election_id)
        
        # Check if voting is open
        if election.current_phase != 'voting':
            return jsonify({'success': False, 'message': 'Voting is not currently open'})
        
        # Check if user is a chama member
        user_role = get_user_chama_role(current_user.id, election.chama_id)
        if not user_role:
            return jsonify({'success': False, 'message': 'You must be a chama member to vote'})
        
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        
        if not candidate_id:
            return jsonify({'success': False, 'message': 'Please select a candidate'})
        
        # Check if candidate exists
        candidate = ElectionCandidate.query.get(candidate_id)
        if not candidate or candidate.election_id != election_id:
            return jsonify({'success': False, 'message': 'Invalid candidate'})
        
        # Check if user has already voted
        existing_vote = ElectionVote.query.filter_by(
            election_id=election_id,
            voter_id=current_user.id
        ).first()
        
        if existing_vote:
            return jsonify({'success': False, 'message': 'You have already voted in this election'})
        
        # Cast vote
        vote = ElectionVote(
            election_id=election_id,
            candidate_id=candidate_id,
            voter_id=current_user.id
        )
        
        db.session.add(vote)
        
        # Update total votes
        election.total_votes = ElectionVote.query.filter_by(election_id=election_id).count() + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Vote cast successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error casting vote: {e}")
        return jsonify({'success': False, 'message': str(e)})

@elections_bp.route('/<int:election_id>/finalize', methods=['POST'])
@login_required
def finalize_election(election_id):
    """Finalize election and assign winner to leadership role"""
    try:
        election = LeadershipElection.query.get_or_404(election_id)
        
        # Check if user can finalize elections
        if not election.chama.can_user_access_feature(current_user.id, 'create_elections'):
            return jsonify({'success': False, 'message': 'You do not have permission to finalize elections'})
        
        # Check if election is completed
        if election.current_phase != 'completed':
            return jsonify({'success': False, 'message': 'Election is not yet completed'})
        
        if election.status == 'completed':
            return jsonify({'success': False, 'message': 'Election has already been finalized'})
        
        # Get results
        results = election.get_results()
        
        if not results:
            return jsonify({'success': False, 'message': 'No votes were cast in this election'})
        
        # Determine winner (candidate with most votes)
        winner_result = results[0]
        winner_candidate_id = winner_result.candidate_id
        winner_votes = winner_result.vote_count
        
        # Update election
        election.winner_id = winner_candidate_id
        election.status = 'completed'
        
        # Remove current holder of this position
        db.session.execute(
            chama_members.update().where(
                and_(
                    chama_members.c.chama_id == election.chama_id,
                    chama_members.c.role == election.position
                )
            ).values(role='member')
        )
        
        # Assign new leadership role
        election.chama.assign_leadership_role(winner_candidate_id, election.position)
        
        db.session.commit()
        
        # Notify winner and all members
        from app.models.notification import Notification
        winner = User.query.get(winner_candidate_id)
        
        # Notify winner
        notification = Notification(
            user_id=winner_candidate_id,
            chama_id=election.chama_id,
            title=f'Congratulations! You won the election',
            message=f'You have been elected as {election.position.title()} of {election.chama.name} with {winner_votes} votes!',
            type='election_won',
            related_id=election.id
        )
        db.session.add(notification)
        
        # Notify all members
        members = db.session.query(chama_members.c.user_id).filter(
            chama_members.c.chama_id == election.chama_id
        ).all()
        
        for member_id_tuple in members:
            member_id = member_id_tuple[0]
            if member_id != winner_candidate_id:  # Don't notify winner twice
                notification = Notification(
                    user_id=member_id,
                    chama_id=election.chama_id,
                    title=f'Election Results: {election.position.title()}',
                    message=f'{winner.username} has been elected as the new {election.position.title()} of {election.chama.name}!',
                    type='election_results',
                    related_id=election.id
                )
                db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Election finalized! {winner.username} is the new {election.position.title()}',
            'winner': winner.username
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error finalizing election: {e}")
        return jsonify({'success': False, 'message': str(e)})
