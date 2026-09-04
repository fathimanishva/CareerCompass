import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import (
    db, User, Skill, CareerRole, CareerSkillRequirement,
    LearningResource, Certification, ProjectIdea, UserRoadmapProgress
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('student.dashboard'))


@admin_bp.route('/dashboard')
def dashboard():
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_careers = CareerRole.query.count()
    total_skills = Skill.query.count()
    total_resources = LearningResource.query.count()
    total_certs = Certification.query.count()
    
    # Career popularity
    careers = CareerRole.query.all()
    career_stats = []
    for c in careers:
        user_count = User.query.filter_by(target_career_id=c.id).count()
        career_stats.append({
            'career': c,
            'user_count': user_count
        })
    career_stats.sort(key=lambda x: x['user_count'], reverse=True)
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_students=total_students,
        total_careers=total_careers,
        total_skills=total_skills,
        total_resources=total_resources,
        total_certs=total_certs,
        career_stats=career_stats,
        recent_users=recent_users
    )


# ---------------- Careers CRUD ----------------
@admin_bp.route('/careers')
def careers_list():
    careers = CareerRole.query.all()
    return render_template('admin/careers.html', careers=careers)


@admin_bp.route('/careers/create', methods=['GET', 'POST'])
def career_create():
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        average_salary = request.form.get('average_salary', '$90,000 - $140,000 / yr').strip()
        market_demand = request.form.get('market_demand', 'High')
        difficulty = request.form.get('difficulty', 'Intermediate')
        icon = request.form.get('icon', 'fa-laptop-code').strip()
        
        if not title or not category or not description:
            flash('Title, category, and description are required.', 'warning')
            return render_template('admin/career_form.html', all_skills=all_skills, career=None)
            
        if CareerRole.query.filter_by(title=title).first():
            flash('A career role with this title already exists.', 'danger')
            return render_template('admin/career_form.html', all_skills=all_skills, career=None)
            
        new_career = CareerRole(
            title=title,
            category=category,
            description=description,
            average_salary=average_salary,
            market_demand=market_demand,
            difficulty=difficulty,
            icon=icon
        )
        db.session.add(new_career)
        db.session.flush()
        
        # Process selected skills
        selected_skills = request.form.getlist('skill_ids')
        for sid in selected_skills:
            importance = request.form.get(f'importance_{sid}', 'Critical')
            target_prof = request.form.get(f'proficiency_{sid}', 'Intermediate')
            weight = 3 if importance == 'Critical' else (2 if importance == 'Recommended' else 1)
            
            req = CareerSkillRequirement(
                career_id=new_career.id,
                skill_id=int(sid),
                importance=importance,
                target_proficiency=target_prof,
                weight=weight
            )
            db.session.add(req)
            
        db.session.commit()
        flash(f'Career role "{title}" created successfully!', 'success')
        return redirect(url_for('admin.careers_list'))
        
    return render_template('admin/career_form.html', all_skills=all_skills, career=None)


@admin_bp.route('/careers/edit/<int:career_id>', methods=['GET', 'POST'])
def career_edit(career_id):
    career = CareerRole.query.get_or_404(career_id)
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()
    existing_reqs = {r.skill_id: r for r in career.skill_requirements}
    
    if request.method == 'POST':
        career.title = request.form.get('title', '').strip()
        career.category = request.form.get('category', '').strip()
        career.description = request.form.get('description', '').strip()
        career.average_salary = request.form.get('average_salary', '').strip()
        career.market_demand = request.form.get('market_demand', 'High')
        career.difficulty = request.form.get('difficulty', 'Intermediate')
        career.icon = request.form.get('icon', 'fa-laptop-code').strip()
        
        # Clear and rebuild requirements
        CareerSkillRequirement.query.filter_by(career_id=career.id).delete()
        
        selected_skills = request.form.getlist('skill_ids')
        for sid in selected_skills:
            importance = request.form.get(f'importance_{sid}', 'Critical')
            target_prof = request.form.get(f'proficiency_{sid}', 'Intermediate')
            weight = 3 if importance == 'Critical' else (2 if importance == 'Recommended' else 1)
            
            req = CareerSkillRequirement(
                career_id=career.id,
                skill_id=int(sid),
                importance=importance,
                target_proficiency=target_prof,
                weight=weight
            )
            db.session.add(req)
            
        db.session.commit()
        flash(f'Career role "{career.title}" updated successfully!', 'success')
        return redirect(url_for('admin.careers_list'))
        
    return render_template(
        'admin/career_form.html',
        all_skills=all_skills,
        career=career,
        existing_reqs=existing_reqs
    )


@admin_bp.route('/careers/delete/<int:career_id>', methods=['POST'])
def career_delete(career_id):
    career = CareerRole.query.get_or_404(career_id)
    title = career.title
    db.session.delete(career)
    db.session.commit()
    flash(f'Career role "{title}" deleted successfully.', 'info')
    return redirect(url_for('admin.careers_list'))


# ---------------- Skills & Resources CRUD ----------------
@admin_bp.route('/skills', methods=['GET', 'POST'])
def skills_list():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not category:
            flash('Skill name and category are required.', 'warning')
        elif Skill.query.filter_by(name=name).first():
            flash('A skill with this name already exists.', 'danger')
        else:
            new_skill = Skill(name=name, category=category, description=description)
            db.session.add(new_skill)
            db.session.commit()
            flash(f'Skill "{name}" added successfully!', 'success')
            
        return redirect(url_for('admin.skills_list'))
        
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    categories = [s[0] for s in Skill.query.with_entities(Skill.category).distinct()]
    return render_template('admin/skills.html', skills=skills, categories=categories)


@admin_bp.route('/skills/delete/<int:skill_id>', methods=['POST'])
def skill_delete(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    name = skill.name
    db.session.delete(skill)
    db.session.commit()
    flash(f'Skill "{name}" deleted.', 'info')
    return redirect(url_for('admin.skills_list'))


@admin_bp.route('/resources', methods=['GET', 'POST'])
def resources_list():
    careers = CareerRole.query.all()
    skills = Skill.query.order_by(Skill.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        resource_type = request.form.get('resource_type', 'Course')
        url = request.form.get('url', '').strip()
        provider = request.form.get('provider', '').strip()
        is_free = bool(request.form.get('is_free'))
        difficulty = request.form.get('difficulty', 'Beginner')
        career_id = request.form.get('career_id')
        skill_id = request.form.get('skill_id')
        description = request.form.get('description', '').strip()
        
        if not title or not url:
            flash('Title and URL are required.', 'warning')
        else:
            res = LearningResource(
                title=title,
                resource_type=resource_type,
                url=url,
                provider=provider or 'Online',
                is_free=is_free,
                difficulty=difficulty,
                career_id=int(career_id) if career_id and career_id.isdigit() else None,
                skill_id=int(skill_id) if skill_id and skill_id.isdigit() else None,
                description=description
            )
            db.session.add(res)
            db.session.commit()
            flash(f'Resource "{title}" created successfully!', 'success')
            
        return redirect(url_for('admin.resources_list'))
        
    resources = LearningResource.query.all()
    return render_template('admin/resources.html', resources=resources, careers=careers, skills=skills)


@admin_bp.route('/resources/delete/<int:resource_id>', methods=['POST'])
def resource_delete(resource_id):
    res = LearningResource.query.get_or_404(resource_id)
    title = res.title
    db.session.delete(res)
    db.session.commit()
    flash(f'Resource "{title}" deleted.', 'info')
    return redirect(url_for('admin.resources_list'))


# ---------------- Users Oversight ----------------
@admin_bp.route('/users')
def users_list():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle-role/<int:user_id>', methods=['POST'])
def toggle_user_role(user_id):
    if current_user.id == user_id:
        flash('You cannot change your own administrator status.', 'warning')
        return redirect(url_for('admin.users_list'))
        
    user = User.query.get_or_404(user_id)
    user.role = 'student' if user.role == 'admin' else 'admin'
    db.session.commit()
    flash(f'Updated role for {user.full_name} to {user.role}.', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def user_delete(user_id):
    if current_user.id == user_id:
        flash('You cannot delete your own account from the admin portal.', 'danger')
        return redirect(url_for('admin.users_list'))
        
    user = User.query.get_or_404(user_id)
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{name}" deleted.', 'info')
    return redirect(url_for('admin.users_list'))
