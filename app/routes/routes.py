import base64
import os
import shutil
from typing import OrderedDict
import uuid
from flask import Blueprint, current_app, flash, json, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename 
from app.db import db
from app.classes.SCORMparser import SCORMParser
from app.classes.forms import ProfileForm, UploadForm, FeedbackForm
from app.classes.helper import generate_math_captcha, get_lrs_query_string
from app.models import Course, User, UserCourse
from app.models.block import Block
from app.models.district import District
from app.models.feedback import Feedback
from app.models.state_ut import State_UT


blp = Blueprint("routes",__name__)

@blp.route("/")
def index():
    return render_template('index.html')

@blp.route("/contact")
def contact():
    return render_template('other/contact.html')

@blp.route("/feedback", methods=['GET','POST'])
def feedback():
    form = FeedbackForm()
    if request.method == "POST":
        name = current_user.name
        email = current_user.email
        subject = request.form.get('subject', '').strip()
        message_category = request.form.get('message_type', '').strip()
        rating = request.form.get('rating') or request.form.get('rating-mobile')
        captcha_response = request.form.get('captcha_answer','').strip()
        message = request.form.get('message', '').strip()

        if not subject or not (1 <= len(subject) <= 100):
            flash("Subject is required (max 100 characters).")
            return redirect(url_for('routes.feedback'))
        allowed_categories = {'course', 'technical', 'subject_related', 'admin', 'others'}
        if not message_category or message_category not in allowed_categories:
            flash("Invalid message category.","error")
            return redirect(url_for('routes.feedback'))
        if rating:
            try:
                int_rating = int(rating)
                if int_rating < 1 or int_rating > 5:
                    raise ValueError
            except Exception:
                flash("Rating must be a number between 1 and 5.","error")
                return redirect(url_for('routes.feedback'))
        if not captcha_response:
            flash('Please fill the captcha.')
            return redirect(url_for('routes.feedback'))
        
        captcha_answer = int(session.get('captcha_answer'))
        captcha_response = int(captcha_response)
        verification_response = captcha_answer == captcha_response
        if not verification_response:
            flash('CAPTCHA verification failed. Please try again.', "error")
            return redirect(url_for('routes.feedback'))
        
        try:
            feedback = Feedback(
                name=name,
                email=email,
                subject=subject,
                message_category=message_category,
                message=message,
                rating=int_rating if rating else 0
            )
            feedback.save_to_db()
            # activity_logger.info(f"Feedback submitted by {email}")
            flash("Thank you for sharing your feedback.", "success")
        except Exception as ex:
            # error_logger.error(f"Error saving feedback: {ex}")
            flash("There was an error submitting your feedback. Please try again later.", "error")
        return redirect(url_for('routes.feedback'))

    captcha_question = generate_math_captcha()
    return render_template('other/feedback.html', form = form, captcha_question = captcha_question)

@blp.route('/faq')
def faq():
    # access_logger.info("Visited FAQ page")
    return render_template('other/faq.html')

@blp.route('/pdf/<string:pdf_name>')
@login_required
def view_pdf(pdf_name):
    filename = f"{pdf_name}.pdf"
    pdf_title = ""
    if pdf_name == 'training_manual':
        pdf_title = 'Yuktdhara Manual'
    else:
        pdf_title = 'Yuktdhara Leaflet'
    return render_template('other/pdf_viewer.html', filename=filename, pdf_title=pdf_title)

@blp.route('/update_profile')
def update_profile():
    profile = None
    if current_user.is_authenticated:
        profile = User.get_user_by_id(current_user.id)
    form = ProfileForm(obj=profile)
    if request.method == "POST":
        import re

        email = request.form.get('email', '').strip()
        name = request.form.get('full_name', '').strip()
        state_id = request.form.get('state','').strip()
        district_id = request.form.get('district','').strip()
        block_id = request.form.get('block','').strip()
        captcha_response = request.form.get('captcha_answer','').strip()

        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Please enter a valid email address.','danger')
            return redirect(url_for('routes.update_profile'))
        if not name or not re.match(r'^[A-Za-z0-9_ ]{3,20}$', name):
            flash('Username must be 3-20 characters, only letters, numbers, underscores, and spaces.','danger')
            return redirect(url_for('routes.update_profile'))
        
        if not captcha_response:
            flash('Please fill the captcha.','danger')
            return redirect(url_for('routes.update_profile'))

        captcha_answer = int(session.get('captcha_answer'))
        captcha_response = int(captcha_response)
        verification_response = captcha_answer == captcha_response
        if not verification_response:
            flash('CAPTCHA verification failed. Please try again.','danger')
            return redirect(url_for('routes.update_profile'))

        user = User.query.filter_by(email=email).first()
        if user:
            user.name = name
            user.state_id = state_id
            user.district_id = district_id
            user.block_id = block_id
            db.session.commit()
        

        # activity_logger.info(f"User updated: {email}")
        flash("You have Successfully updated your profile.","success")
        return redirect(url_for('routes.update_profile'))
    states = State_UT.get_states()
    form.state.choices = [(0, '-- Select State --')] + \
                           [(str(s.id), s.name.upper()) for s in states]  
      
    if current_user.is_authenticated:
        profile = User.get_user_by_id(current_user.id)
        # profile = profile.json()
        form.state.data = str(profile.state_id)

        districts = District.query.filter_by(state_id=profile.state_id).all()
        form.district.choices = [(0, '-- Select District --')] + \
                                [(str(d.id), d.name.upper()) for d in districts]
        form.district.data = str(profile.district_id)
        
        blocks = Block.query.filter_by(state_id=profile.state_id, district_id=profile.district_id).all()
        form.block.choices = [(0, '-- Select block --')] + \
                                [(str(b.id), b.name.upper()) for b in blocks]
        form.block.data = str(profile.block_id)
        form.full_name.data = profile.name
        form.email.data = profile.email

    captcha_question = generate_math_captcha()
    return render_template('other/profile.html', form = form, captcha_question=captcha_question, 
                           states=states, user_data=profile)

@blp.route('/view/<string:filename>')
@login_required
def render_pdf(filename):
    file_path = "app/static/pdfs"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    abs_package_path = os.path.join(BASE_DIR.split("/app")[0], file_path)
    
    return send_from_directory(abs_package_path, filename)

# LMS related 
@blp.route("/upload", methods=['GET','POST'])
@login_required
def upload():
    form = UploadForm()
    try:
        if request.method == 'POST':
            if 'scorm_file' not in request.files:
                return jsonify({'error': 'No file selected'}), 400
            
            file = request.files['scorm_file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file and file.filename.endswith('.zip'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if not os.path.exists(file_path):
                    file.save(file_path)
                
                # Generate unique package ID
                package_id = str(uuid.uuid4())
                extract_path = os.path.join(current_app.config['SCORM_FOLDER'], package_id)
                title = request.form.get('course_title')
                description = request.form.get('description')
                
                # Parse SCORM package
                parser = SCORMParser(file_path, extract_path, package_id, title, description)
                if parser.extract_package():
                    # Save course to database
                    course = Course(
                        name=parser.title,
                        description=parser.description,
                        scorm_version=parser.scorm_version,
                        package_path=parser.package_path,
                        manifest_path=parser.manifest_path,
                        manifest_identifier=parser.manifest_identifier,
                        manifest_title=parser.manifest_title,
                        package_id=parser.package_id,
                        launch_url=parser.launch_url)
                    if parser.duplicate_package_path:
                        course.update()
                        shutil.rmtree(parser.duplicate_package_path)
                    else:
                        course.save()
                    
                    # Clean up uploaded zip file
                    os.remove(file_path)
                    flash(message="SCORM package uploaded successfully",category="success" )
                    return redirect(url_for('routes.courses'))
                    # return jsonify({'success': True, 'course_id': course_id, 'message': 'SCORM package uploaded successfully'})
                else:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    shutil.rmtree(extract_path,ignore_errors=True)
                    flash(message= f'SCORM package with manifest ID already exists',category="error" )
                    # return jsonify({'error': 'Invalid SCORM package'}), 400
            else:
                flash(message= f'Please upload a ZIP file',category="error" )
                # return jsonify({'error': 'Please upload a ZIP file'}), 400
    except Exception as ex:
        if os.path.isfile(file_path):
            os.remove(file_path)
        shutil.rmtree(extract_path, ignore_errors=True)
        flash(message= f'There was an error while uploading {ex}',category="error" )
        # return redirect(url_for('routes.upload'))
        # return jsonify({'error': f'There was an error while uploading {ex}'}), 400
    return render_template('/lms/upload.html', form=form)

@blp.route('/courses')
@login_required
def courses():
    courses = Course.find_all()
    user = User.get_user_by_id(current_user.id)
    return render_template('lms/courses.html', courses=courses, user=user)

@blp.route('/course/<int:course_id>')
@login_required
def launch(course_id):
    course = Course.find_by_id(course_id)
    user = current_user
    return render_template('lms/launch.html', course=course, user=user)

@blp.route('/launch/<int:course_id>')
@login_required
def launch_course(course_id):
    user = User.get_user_by_id(current_user.id)
    course = Course.find_by_id(course_id)
    base_url = request.url_root.rstrip('/')
    if not UserCourse.find_by_user_and_course_id(user.id,course.id):
        user_course = UserCourse(user_id=user.id, course_id=course.id, certificate_issued=False)
        user_course.save()
    query_string = get_lrs_query_string(user, base_url)
           
    return render_template('lms/player.html', course=course, course_id = course.id, query_string=query_string)

@blp.route('/scorm/<int:course_id>/<path:filename>')
@login_required
def serve_scorm_content(course_id, filename):
    course = Course.find_by_id(course_id=course_id)
    
    if not course:
        return "Course not found", 404
    # filename = filename + "?resume=8"
    package_path = course.package_path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    abs_package_path = os.path.join(BASE_DIR.split("/routes")[0], package_path.split("app/")[1])
    
    return send_from_directory(abs_package_path, filename)



