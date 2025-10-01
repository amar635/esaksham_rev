import re
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user,login_manager, logout_user
from app.classes.forms import ChangePasswordForm, LoginForm, RegisterForm
from app.classes.helper import decrypt_password, generate_math_captcha
from app.models import User
from passlib.hash import pbkdf2_sha256


blp = Blueprint('auth', __name__, url_prefix='/auth')

@blp.route('/login', methods=['GET','POST'])
def login():
    # Already logged in → redirect
    if current_user.is_authenticated:
        return redirect(url_for('routes.courses'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.username.data.strip().lower()
        password = decrypt_password(form.password.data or "")
        captcha_response = request.form.get('captcha_answer','').strip()

        # Check CAPTCHA first
        expected_captcha = session.get('captcha_answer')
        if not expected_captcha or captcha_response != expected_captcha:
            flash("Invalid CAPTCHA answer. Please try again.", "danger")
            captcha_question = generate_math_captcha()
            return render_template('auth/login.html', form=form, captcha_question=captcha_question)


        user = User.get_user_by_email(email)

        if user and pbkdf2_sha256.verify(password, user.password):
            login_user(user, remember=form.remember_me.data)
            session.pop('captcha_answer', None)  # clear captcha on success

            # Flask-Login handles secure cookie sessions automatically
            next_page = request.args.get('next')
            return redirect(next_page or url_for('routes.courses'))
        # else send message to the frontend
        flash("Invalid username or password", "error")

    captcha_question = generate_math_captcha()
    return render_template('auth/login.html', form=form, captcha_question=captcha_question)

@blp.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if request.method == "POST":
        try:            
            full_name=request.form.get('full_name')
            email=request.form.get('email')
            password=decrypt_password(request.form.get('password'))
            state_id=request.form.get('state')
            district_id=request.form.get('district')
            block_id=request.form.get('block')
            user = User(name=full_name, 
                        email=email,
                        password=pbkdf2_sha256.hash(password), 
                        state_id=state_id, 
                        district_id=None if district_id == -1 else district_id,
                        block_id=None if block_id == -1 else block_id)
            # user.save()
            flash(message=f"Registered Successfully. Please login with your crendentials", category="success")
            return redirect(url_for('auth.login'))
        except Exception as ex:
            flash(message=f"There was a problem in registering. Error: {ex}", category="error")
            return redirect(url_for('auth.register'))
    captcha_question = generate_math_captcha()    
    return render_template('auth/register.html', form=form, captcha_question=captcha_question)


@blp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    import re
        
    uuid = current_user.id
    form = ChangePasswordForm()

    if request.method == "POST":
        current_pwd = decrypt_password(request.form.get('old_password', ''))
        new_pass_input = decrypt_password(request.form.get('password', ''))
        confirm_pass_input = decrypt_password(request.form.get('confirm_password', ''))
        
        if not current_pwd or not (8 <= len(current_pwd) <= 32):
            flash('Current password is required and must be 8-32 characters.', 'error')
            return render_template('change_password.html', uuid=uuid)        
        
        password_pattern = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,32}$'
        )
        if not new_pass_input or not password_pattern.match(new_pass_input):
            flash(
                'New password must be 8-32 characters, include upper and lower case letters, a digit, and a special character.','error'
            )
            return render_template('change_password.html', uuid=uuid)
        
        if new_pass_input != confirm_pass_input:
            flash("Both passwords do not match.", 'warning')
            return render_template('auth/change_password.html', uuid=uuid)
        
        new_pass = pbkdf2_sha256.hash(new_pass_input)
        user = User.query.filter_by(id=uuid).first()
        if user:
            db_pass = user.password
            hash_check = pbkdf2_sha256.verify(current_pwd, db_pass)
            if hash_check:
                data = {"password": new_pass}
                User.update_db(data, user.id)
                logout_user()
                # activity_logger.info(f"Password changed for user: {user.email}")
                flash('Password Changed Successfully. Please login with new password to continue','success')
                return redirect(url_for('auth.login'))
            else:
                flash('Please Check Your Old Password and Try Again !! ', 'error')
                return redirect(url_for('auth.change_password', uuid=uuid))
    if request.method == "GET":
        session['password_change_redirected'] = False
        return render_template('auth/change_password.html', uuid=uuid, form=form)

@blp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))