from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, CareerRole

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)
            
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
            
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    careers = CareerRole.query.all()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        education = request.form.get('education', '').strip()
        target_career_id = request.form.get('target_career_id')
        
        if not full_name or not email or not password:
            flash('Please fill in all required fields.', 'warning')
            return render_template('auth/register.html', careers=careers)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', careers=careers)
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('auth/register.html', careers=careers)
            
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in.', 'danger')
            return render_template('auth/register.html', careers=careers)
            
        new_user = User(
            full_name=full_name,
            email=email,
            role='student',
            education=education,
            target_career_id=int(target_career_id) if target_career_id and target_career_id.isdigit() else None
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Account created successfully! Let\'s set up your skills.', 'success')
        return redirect(url_for('student.skill_profile'))
        
    return render_template('auth/register.html', careers=careers)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    reset_link = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.get_reset_token()
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            flash('Password reset link generated! In production, this is sent to your registered email.', 'success')
            return render_template('auth/forgot_password.html', reset_link=reset_link, email=email)
        else:
            flash('If an account with that email exists, a password reset link has been issued.', 'info')
            
    return render_template('auth/forgot_password.html', reset_link=reset_link)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
        
    user = User.verify_reset_token(token)
    if not user:
        flash('The password reset token is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('auth/reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        user.set_password(password)
        db.session.commit()
        
        flash('Your password has been successfully updated! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', token=token)
