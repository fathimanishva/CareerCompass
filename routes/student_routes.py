import os
import json
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (
    db, User, Skill, UserSkill, CareerRole, CareerSkillRequirement,
    LearningResource, Certification, ProjectIdea, UserRoadmapProgress, DailyLog
)
from services.gap_analyzer import analyze_skill_gap, find_top_career_matches
from services.resume_parser import extract_text_from_file, extract_skills_from_text
from services.ai_service import (
    generate_personalized_roadmap, generate_mock_interview_questions, answer_career_query
)

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
@login_required
def check_student_access():
    pass


@student_bp.route('/dashboard')
def dashboard():
    user = current_user
    target_career = user.target_career
    
    gap_analysis = None
    if target_career:
        gap_analysis = analyze_skill_gap(user, target_career)
        
    top_matches = find_top_career_matches(user, limit=4)
    
    # Active roadmap progress
    roadmap_progress = None
    if target_career:
        roadmap_progress = UserRoadmapProgress.query.filter_by(
            user_id=user.id, career_id=target_career.id
        ).first()
        
    # Recent daily logs
    recent_logs = DailyLog.query.filter_by(user_id=user.id).order_by(DailyLog.date.desc()).limit(5).all()
    total_hours = sum([log.hours_spent for log in DailyLog.query.filter_by(user_id=user.id).all()])
    
    # User skills list
    user_skills = UserSkill.query.filter_by(user_id=user.id).all()
    
    return render_template(
        'student/dashboard.html',
        user=user,
        target_career=target_career,
        gap_analysis=gap_analysis,
        top_matches=top_matches,
        roadmap_progress=roadmap_progress,
        recent_logs=recent_logs,
        total_hours=total_hours,
        user_skills=user_skills
    )


@student_bp.route('/skills', methods=['GET', 'POST'])
def skill_profile():
    user = current_user
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()
    user_skills = UserSkill.query.filter_by(user_id=user.id).all()
    user_skill_ids = [us.skill_id for us in user_skills]
    
    # Group skills by category for easy selection
    skills_by_category = {}
    for skill in all_skills:
        skills_by_category.setdefault(skill.category, []).append(skill)
        
    return render_template(
        'student/skill_profile.html',
        user=user,
        user_skills=user_skills,
        user_skill_ids=user_skill_ids,
        skills_by_category=skills_by_category,
        all_skills=all_skills
    )


@student_bp.route('/skills/add', methods=['POST'])
def add_skill():
    skill_id = request.form.get('skill_id')
    proficiency = request.form.get('proficiency', 'Intermediate')
    years_exp = request.form.get('years_experience', 1.0)
    
    try:
        years_exp = float(years_exp)
    except (ValueError, TypeError):
        years_exp = 1.0
        
    if not skill_id:
        flash('Please select a valid skill.', 'warning')
        return redirect(url_for('student.skill_profile'))
        
    skill = Skill.query.get(skill_id)
    if not skill:
        flash('Skill not found.', 'danger')
        return redirect(url_for('student.skill_profile'))
        
    existing = UserSkill.query.filter_by(user_id=current_user.id, skill_id=skill.id).first()
    if existing:
        existing.proficiency = proficiency
        existing.years_experience = years_exp
        flash(f'Updated proficiency for {skill.name}.', 'info')
    else:
        new_us = UserSkill(
            user_id=current_user.id,
            skill_id=skill.id,
            proficiency=proficiency,
            years_experience=years_exp
        )
        db.session.add(new_us)
        flash(f'Added {skill.name} to your skill profile!', 'success')
        
    db.session.commit()
    return redirect(url_for('student.skill_profile'))


@student_bp.route('/skills/remove/<int:user_skill_id>', methods=['POST'])
def remove_skill(user_skill_id):
    us = UserSkill.query.filter_by(id=user_skill_id, user_id=current_user.id).first_or_404()
    skill_name = us.skill.name
    db.session.delete(us)
    db.session.commit()
    flash(f'Removed {skill_name} from your profile.', 'info')
    return redirect(url_for('student.skill_profile'))


@student_bp.route('/skills/parse-resume', methods=['POST'])
def parse_resume():
    extracted_text = ""
    
    # Check if a file was uploaded
    if 'resume_file' in request.files and request.files['resume_file'].filename:
        file = request.files['resume_file']
        filename = secure_filename(file.filename)
        
        # Ensure uploads folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
        file.save(file_path)
        
        extracted_text = extract_text_from_file(file_path)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except Exception:
            pass
            
    # Check if text was pasted
    pasted_text = request.form.get('resume_text', '').strip()
    if pasted_text:
        extracted_text += "\n" + pasted_text
        
    if not extracted_text.strip():
        flash('No text or readable resume file was provided.', 'warning')
        return redirect(url_for('student.skill_profile'))
        
    extraction_result = extract_skills_from_text(extracted_text)
    matched_skills = extraction_result['matched_skills']
    
    added_count = 0
    existing_user_skill_ids = [us.skill_id for us in current_user.user_skills]
    
    for skill in matched_skills:
        if skill.id not in existing_user_skill_ids:
            us = UserSkill(
                user_id=current_user.id,
                skill_id=skill.id,
                proficiency='Intermediate',
                years_experience=1.0
            )
            db.session.add(us)
            added_count += 1
            
    db.session.commit()
    
    if added_count > 0:
        flash(f'Successfully parsed resume! Automatically added {added_count} new skills to your profile.', 'success')
    else:
        flash(f'Found {len(matched_skills)} skills in your resume, all of which were already in your profile.', 'info')
        
    return redirect(url_for('student.skill_profile'))


@student_bp.route('/careers/explore')
def career_matcher():
    user = current_user
    top_matches = find_top_career_matches(user, limit=20)
    all_careers = CareerRole.query.all()
    return render_template(
        'student/career_matcher.html',
        user=user,
        top_matches=top_matches,
        all_careers=all_careers
    )


@student_bp.route('/careers/set-target/<int:career_id>', methods=['POST'])
def set_target_career(career_id):
    career = CareerRole.query.get_or_404(career_id)
    current_user.target_career_id = career.id
    db.session.commit()
    flash(f'Target career set to {career.title}!', 'success')
    return redirect(url_for('student.gap_analysis', career_id=career.id))


@student_bp.route('/gap-analysis')
@student_bp.route('/gap-analysis/<int:career_id>')
def gap_analysis(career_id=None):
    user = current_user
    
    if career_id:
        target_career = CareerRole.query.get_or_404(career_id)
    elif user.target_career:
        target_career = user.target_career
    else:
        target_career = CareerRole.query.first()
        
    if not target_career:
        flash('No career roles found in database.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    analysis = analyze_skill_gap(user, target_career)
    all_careers = CareerRole.query.all()
    
    # Recommended resources for missing skills
    missing_skill_ids = [m['skill'].id for m in analysis['missing_critical_skills'] + analysis['missing_recommended_skills']]
    recommended_resources = LearningResource.query.filter(
        (LearningResource.career_id == target_career.id) | 
        (LearningResource.skill_id.in_(missing_skill_ids) if missing_skill_ids else False)
    ).limit(8).all()
    
    certifications = Certification.query.filter_by(career_id=target_career.id).all()
    projects = ProjectIdea.query.filter_by(career_id=target_career.id).all()
    
    return render_template(
        'student/gap_analysis.html',
        user=user,
        career=target_career,
        analysis=analysis,
        all_careers=all_careers,
        recommended_resources=recommended_resources,
        certifications=certifications,
        projects=projects,
        radar_json=json.dumps(analysis['radar_chart_data'])
    )


@student_bp.route('/roadmap')
@student_bp.route('/roadmap/<int:career_id>')
def roadmap(career_id=None):
    user = current_user
    
    if career_id:
        target_career = CareerRole.query.get_or_404(career_id)
    elif user.target_career:
        target_career = user.target_career
    else:
        target_career = CareerRole.query.first()
        
    if not target_career:
        flash('No career roles found.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    gap_analysis = analyze_skill_gap(user, target_career)
    generated_plan = generate_personalized_roadmap(user, target_career, gap_analysis)
    
    # Load user progress
    user_progress = UserRoadmapProgress.query.filter_by(
        user_id=user.id, career_id=target_career.id
    ).first()
    
    completed_milestones = user_progress.get_completed_milestones() if user_progress else []
    
    # Calculate progress %
    all_milestones = []
    for phase in generated_plan['phases']:
        all_milestones.extend(phase['milestones'])
        
    total_milestones_count = len(all_milestones)
    completed_count = len(set(completed_milestones).intersection(set(all_milestones)))
    progress_pct = round((completed_count / total_milestones_count * 100), 1) if total_milestones_count > 0 else 0
    
    return render_template(
        'student/roadmap.html',
        user=user,
        career=target_career,
        gap_analysis=gap_analysis,
        plan=generated_plan,
        completed_milestones=completed_milestones,
        progress_pct=progress_pct,
        total_milestones=total_milestones_count,
        completed_count=completed_count,
        user_progress=user_progress
    )


@student_bp.route('/roadmap/toggle-milestone', methods=['POST'])
def toggle_milestone():
    data = request.get_json() or {}
    career_id = data.get('career_id')
    milestone_text = data.get('milestone')
    is_completed = data.get('completed', False)
    
    if not career_id or not milestone_text:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
    progress = UserRoadmapProgress.query.filter_by(
        user_id=current_user.id, career_id=career_id
    ).first()
    
    if not progress:
        progress = UserRoadmapProgress(
            user_id=current_user.id,
            career_id=career_id,
            completed_milestones_json='[]',
            progress_percentage=0.0
        )
        db.session.add(progress)
        
    completed_list = progress.get_completed_milestones()
    
    if is_completed:
        if milestone_text not in completed_list:
            completed_list.append(milestone_text)
    else:
        if milestone_text in completed_list:
            completed_list.remove(milestone_text)
            
    progress.set_completed_milestones(completed_list)
    
    # Recalculate %
    total_milestones = data.get('total_milestones', 12)
    if total_milestones > 0:
        progress.progress_percentage = round((len(completed_list) / total_milestones) * 100, 1)
        
    db.session.commit()
    
    return jsonify({
        'success': True,
        'completed_count': len(completed_list),
        'progress_percentage': progress.progress_percentage
    })


@student_bp.route('/resources')
def resources():
    category = request.args.get('type')
    is_free = request.args.get('free')
    
    query = LearningResource.query
    if category:
        query = query.filter_by(resource_type=category)
    if is_free == 'true':
        query = query.filter_by(is_free=True)
        
    all_resources = query.all()
    all_types = [r[0] for r in LearningResource.query.with_entities(LearningResource.resource_type).distinct()]
    
    return render_template(
        'student/resources.html',
        resources=all_resources,
        types=all_types,
        selected_type=category,
        is_free=is_free
    )


@student_bp.route('/projects')
def projects():
    difficulty = request.args.get('difficulty')
    query = ProjectIdea.query
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    all_projects = query.all()
    
    return render_template(
        'student/projects.html',
        projects=all_projects,
        selected_difficulty=difficulty
    )


@student_bp.route('/certifications')
def certifications():
    all_certs = Certification.query.all()
    return render_template('student/certifications.html', certifications=all_certs)


@student_bp.route('/ai-tools', methods=['GET', 'POST'])
def ai_tools():
    user = current_user
    target_career = user.target_career or CareerRole.query.first()
    
    interview_questions = []
    ai_response = None
    query_text = ""
    
    if target_career:
        interview_questions = generate_mock_interview_questions(target_career, [], [])
        
    if request.method == 'POST':
        query_text = request.form.get('query', '').strip()
        if query_text:
            ai_response = answer_career_query(user, query_text)
            
    return render_template(
        'student/ai_tools.html',
        user=user,
        target_career=target_career,
        interview_questions=interview_questions,
        ai_response=ai_response,
        query_text=query_text
    )


@student_bp.route('/log-study', methods=['POST'])
def log_study():
    hours = request.form.get('hours_spent', 1.0)
    topic = request.form.get('topic_studied', '').strip()
    notes = request.form.get('notes', '').strip()
    
    try:
        hours = float(hours)
    except (ValueError, TypeError):
        hours = 1.0
        
    log = DailyLog(
        user_id=current_user.id,
        date=date.today(),
        hours_spent=hours,
        topic_studied=topic,
        notes=notes
    )
    db.session.add(log)
    db.session.commit()
    flash(f'Logged {hours} hours of study on "{topic or "General Learning"}"!', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/report')
@student_bp.route('/report/<int:career_id>')
def download_report(career_id=None):
    user = current_user
    career = CareerRole.query.get(career_id) if career_id else user.target_career
    if not career:
        career = CareerRole.query.first()
        
    gap_analysis = analyze_skill_gap(user, career)
    roadmap_plan = generate_personalized_roadmap(user, career, gap_analysis)
    
    return render_template(
        'student/report.html',
        user=user,
        career=career,
        analysis=gap_analysis,
        plan=roadmap_plan,
        generated_at=datetime.utcnow().strftime('%B %d, %Y')
    )
