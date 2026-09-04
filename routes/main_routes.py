from flask import Blueprint, render_template, request
from models import CareerRole, Skill, LearningResource

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    careers = CareerRole.query.all()
    featured_skills = Skill.query.limit(16).all()
    skills_count = Skill.query.count()
    resources_count = LearningResource.query.count()
    return render_template(
        'index.html',
        careers=careers,
        featured_skills=featured_skills,
        skills_count=skills_count,
        resources_count=resources_count
    )


@main_bp.route('/careers')
def explore_careers():
    category = request.args.get('category')
    query = CareerRole.query
    if category:
        query = query.filter_by(category=category)
    careers = query.all()
    
    # Get distinct categories
    categories = db_categories = [c[0] for c in CareerRole.query.with_entities(CareerRole.category).distinct()]
    
    return render_template(
        'careers_list.html',
        careers=careers,
        categories=categories,
        selected_category=category
    )


@main_bp.route('/careers/<int:career_id>')
def career_detail(career_id):
    career = CareerRole.query.get_or_404(career_id)
    return render_template('career_detail.html', career=career)


@main_bp.route('/about')
def about():
    return render_template('about.html')
