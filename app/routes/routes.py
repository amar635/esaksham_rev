import base64
import os
import shutil
from typing import OrderedDict
import uuid
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename 

from app.classes.SCORMparser import SCORMParser
from app.classes.forms import UploadForm
from app.classes.helper import get_lrs_query_string
from app.models import Course, User, UserCourse


blp = Blueprint("routes",__name__)

@blp.route("/")
@login_required
def index():
    return render_template('index.html')

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
def launch(course_id):
    course = Course.find_by_id(course_id)
    return render_template('lms/launch.html', course=course)

@blp.route('/launch/<int:course_id>')
@login_required
def launch_course(course_id):
    user = User.get_user_by_id(current_user.id)
    course = Course.find_by_id(course_id)
    base_url = request.url_root.rstrip('/')
    if not UserCourse.find_by_user_and_course_id(user.id,course.id):
        user_course = UserCourse(user_id=user.id, course_id=course.id, certificate_issued=False)
        user_course.save()
    # actor = {
    #     "mbox": user.email,
    #     "objectType": "Agent",
    #     "name": user.name
    #     }
    # endpoint = '/api/lrs'
    # auth = get_basic_auth(key=user.name,secret_key=user.email)
    query_string = get_lrs_query_string(user,base_url)
    # slxapi=%7B%22actor%22%3A%7B%22mbox%22%3A%22mailto%3Aanonymous%40anonymous.com%22%2C%22objectType%22%3A%22Agent%22%2C%22name%22%3A%22anonymous%22%7D%2C%22endpoint%22%3A%22http%3A%2F%2F127.0.0.1%3A5000{{%2Flrs%2Fxapi}}%22%2C%22auth%22%3A%22{{Basic%20dzI0SnlUbjBTSUVIZlM6VnJRczdmRXVYVnJkQWhOMUVJSDF4cVZDaE1XSjdvQmd4ajM4SjNpMnl3WQ}}%3D%3D%22%7D
    # query_string = 'slxapi=%7B%22actor%22%3A%7B%22mbox%22%3A%22mailto%3Aamar.saxena%40gmail.co%22%2C%22objectType%22%3A%22Agent%22%2C%22name%22%3A%22Amar%20Saxena%22%7D%2C%22endpoint%22%3A%22%2Flrs%2Fapi%22%2C%22auth%22%3A%22Basic%20cHVibGljX2tleTpzZWNyZXRfa2V5%22%7D'
            
    return render_template('lms/player.html', course=course, course_id = course.id, query_string=query_string)

@blp.route('/scorm/<int:course_id>/<path:filename>')
def serve_scorm_content(course_id, filename):
    course = Course.find_by_id(course_id=course_id)
    
    if not course:
        return "Course not found", 404
    # filename = filename + "?resume=8"
    package_path = course.package_path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    abs_package_path = os.path.join(BASE_DIR.split("/routes")[0], package_path.split("app/")[1])
    
    return send_from_directory(abs_package_path, filename)

@blp.route('/dashboard/activity_identification', methods=['GET','POST'])
def activity_identification():
    assets = OrderedDict({
        
        
    })
    gaw = ["GAW", "Non GAW"]
    categories = ["A","B","C","D"]
    clusters = ["Agriculture", "Infrastructure", "NRM"]
    ridges= ["Upper", "Middle", "Lower"]
    beneficiaries = ["Community", "Groups", "Individuals"]
    activities = ["Repair", "Community", "Renovation"]
    slopes= ['00-01%', '01-03%', '03-08%', '08-15%', '15-30%','30-50%', 'Any Slope']
    water_works = [ 'Irrigation', 'SWC', 'GW Recharge', 'Soil Health', 'Other than Water']
    location_specific =['Waste Lands', 'Coastal Area', 'Built-Up Area', 'Agricultural Land', 'Canals', 'Road Side', 'Erosion Affected Area', 'Water bodies', 'Drainage Line', 'Gullied and Ravinous Land', 'Waterlogged Area']
    
    major_scheduled_category = ['Afforestation', 'Irrigation', 'Land Development', 
    'Traditional water bodies', 'Water Conservation',
    'Watershed management','Construction of Biogas plant',
    'Construction of house','Development of fallow/waste lands',
    'Improving liveihoods through','Improving productivity of land',
    'Promotion of fisheries','Promotion of livestock',
    'Common workshed for SHG','Pucca Storage facilities for Agricultural produce',
    'Rural Sanitation','Construction of Building',
    'Construction of Food grain Storage structure',
    'Disaster preparedness/ Restoration','Maintenance',
    'Production of building material','Rural Connectivity',
    'School play field & Compound wall']
    work_types = ['Plantation','Canals','Bunds','Land related works','Renovation of traditional water bodies','Check Dams',
    'Percolation tanks','Ponds','Rain Water Harvesting Structure','Recharge structure','Trenches','Bench Terrace',
    'Biogas Plant','Construction of PMAY /State House','Irrigation Well','Fish drying yard','Azola Cultivation','Livestock shelter',
    'Work shed/building for SHG','Food grain Storage structure','Infrastructure for Liquid Biomanure','Anganwadi Center Building','Crematorium','Cyclone Shelter',
    'Gram Panchayat Building','Kitchen Shed','Village/Rural Haat','Drain/ Drainage','Embankment','Flood/ Diversion Channels',
    'Storm water drains','Border Roads','Building material','Roads','Soak Pit','Solid Liquid Waste Management',
    'Toilets','Govt. School Compound wall','Play Field',]
    permissible_works = ['Afforestation of wastelands using Forestry trees for individuals',
    'Along the coast Afforestation using forestry Trees for Community',
    'Along the coast Block Plantation of Farm Forestry Trees for Community',
    'Along the coast Block Plantation of Forestry Trees for Community',
    'Along the coast Block Plantation of Horticulture Trees for Community',
    'Along the coast Line Plantation of Coastal Shelter Belt Trees for Community',
    'Along the coast Line Plantation of Forestry Trees for Community',
    'Along the coast Line Plantation of Horticulture Trees for Community',
    'Block Plantation of Biodrainage Trees in fields for Community',
    'Block Plantation of Biodrainage Trees in Government building premises for Community',
    'Block Plantation of Biodrainage trees in Wastelands for community',
    'Block Plantation of Farm Forestry Trees in fields for Community',
    'Block Plantation of Farm Forestry Trees in Fields for Individuals',
    'Block Plantation of Farm Forestry Trees in Government building premises for Community',
    'Block Plantation of Forestry Trees in Fields for Community',
    'Block Plantation of Forestry Trees in Fields for Individuals',
    'Block Plantation of Forestry Trees in Government building premises for Community',
    'Block Plantation of Horticulture Trees in Government building premises for Community',
    'Block Plantation of Sericulture Trees in Fields for Community',
    'Block Plantation of Shelter Belt Trees for Individuals',
    'Boundary Line Plantation of Farm Forestry Trees for Community',
    'Boundary Line Plantation of Forestry Trees for Community',
    'Boundary Line Plantation of Horticulture Trees for Community',
    'Boundary Line Plantation of Shelter Belt Trees for Community',
    'Canal Line Plantation of Forestry Trees for Community',
    'Canal Line Plantation of Horticulture Trees for Community',
    'Development of Silvipasture Grassslands for Community',
    'Fields Block Plantation of Horticulture Trees for Community',
    'Raising of Nursery for Community',
    'Raising of Nursery for Groups',
    'Road Line Plantation of Shelter Belt Trees for Community',
    'Road side line plantation of Forestry Trees for Community',
    'Wasteland Block Plantation of Farm Forestry Trees for Community',
    'Wasteland Block Plantation of Forestry Trees for Community',
    'Wasteland Block Plantation of Horticulture Trees for Community',
    'Wasteland Block Plantation of Sericulture Trees for Community',
    'Construction of distributary Canal for Community',
    'Construction of Feeder Canal for Community',
    'Construction of minor Canal for Community',
    'Construction of sub-minor Canal for Community',
    'Construction of water courses for Community',
    'Lining of distributary Canal for Community',
    'Lining of Feeder Canal for Community',
    'Lining of minor Canal for Community',
    'Lining of sub-minor Canal for Community',
    'Lining of water courses Canal for Community',
    'Renovation of distributary Canal for Community',
    'Renovation of Feeder Canal for Community',
    'Renovation of minor Canal for Community',
    'Renovation of sub-minor Canal for Community',
    'Repair and Maintenance of distributary Canal for Community',
    'Repair and Maintenance of Feeder Canal for Community',
    'Repair and Maintenance of minor Canal for Community',
    'Repair and Maintenance of sub-minor Canal for Community',
    'Repair and Maintenance of water course Canal for Community',
    'Construction of Earthen peripheral/farm/field Bund for Community',
    'Construction of Pebble peripheral/farm/field Bund for Community',
    'Construction of Pebble peripheral/farm/field Bund for Individuals',
    'Construction of Stone peripheral/farm/field Bund for Community',
    'Development of chaur Land for Community',
    'Development of Fallow Land for Community',
    'Levelling/shaping of Wasteland Land for Community',
    'Renovation of Community Water Harvesting Ponds for Community',
    'Renovation of Fisheries Ponds for Community',
    'Construction of Earthen Anicut Check Dam for Individuals',
    'Construction of Earthen Check Dam for Community',
    'Construction of Masonry/CC Check Dam for Community',
    'Construction of Masonry/CC Check Dam for Individuals',
    'Construction of Underground Dykes for Community',
    'Repair and Maintenance of Earthen Check Dam for Community',
    'Repair and Maintenance of Masonry/CC Check Dam for Community',
    'Construction of Mini Percolation Tank for Community',
    'Construction of Mini Percolation Tank for Individuals',
    'Repair and maintenance of Mini Percolation Tank for Community',
    'Construction of Community Water Harvesting Ponds',
    'Repair and maintenance of Community Water Harvesting Ponds for Community',
    'Repair and maintenance of Fisheries Ponds for Community',
    'Roof Top Rain Water Harvesting for Government/Panchayat Buildings',
    'Construction of Recharge Pits for Community',
    'Construction of Recharge Pits for Individuals',
    'Construction of Sand filter for borewell recharge for Community',
    'Construction of Sand filter for Borewell recharge for Individual',
    'Construction of Sand filter for openwell recharge for Community',
    'Construction of Sand filter for openwell recharge for Groups',
    'Construction of Sand filter for Openwell recharge for Individual',
    'Construction of Water Absorption Trench for Community',
    'Construction of Level Bench Terrace for Community',
    'Construction of Level Bench Terrace for Individual',
    'Construction of Upland Bench Terrace for Community',
    'Construction of Upland Bench Terrace for Individual',
    'Construction of Earthen contour Bund for Community',
    'Construction of Earthen contour Bund for Individuals',
    'Construction of Earthen graded Bund for Community',
    'Construction of Earthen graded Bund for Individuals',
    'Construction of Pebble contour Bund for Community',
    'Construction of Pebble contour Bund for Individuals',
    'Construction of Pebble graded Bund for Community',
    'Construction of Pebble graded Bund for Individuals',
    'Construction of Stone contour Bund for Community',
    'Construction of Stone contour Bund for Individuals',
    'Construction of Stone graded Bund for Community',
    'Construction of Stone graded Bund for Individuals',
    'Repair and Maintenance of Earthen graded Bund for Community',
    'Repair and Maintenance of Pebble graded Bund for Community',
    'Repair and Maintenance of Stone graded Bund for Community',
    'Construction of Boulder Check Dam for Community',
    'Construction of Boulder Check Dam for Individuals',
    'Construction of Brushwood Check Dam for Community',
    'Construction of Brushwood Check Dam for Individuals',
    'Construction of Earthen Gully Plugs for Community',
    'Construction of Earthen Gully Plugs for Individuals',
    'Construction of Gabion Check Dam for Community',
    'Construction of Gabion Check Dam for Individuals',
    'Construction of Stone boulder Gully Plugs for Community',
    'Construction of Stone boulder Gully Plugs for Individuals',
    'Repair and Maintenance of Boulder Check Dam for Community',
    'Repair and maintenance of Earthen Gully Plugs for Community',
    'Repair and Maintenance of Gabion Check Dam for Community',
    'Repair and maintenance of Stone boulder Gully Plugs for Community',
    'Construction of Continuous Contour Trench for Community',
    'Construction of Staggered Trench for Community',
    'Construction of Bio-gas plant for individual',
    'Unskilled wage component towards the construction of Bio-gas plant for community',
    'Construction of PMAY-G House  Building for Individuals',
    'Construction of State scheme Houses Building for Individuals',
    'Construction of Earthen peripheral/farm/field Bund for Individuals',
    'Construction of Stone peripheral/farm/field Bund for Individuals',
    'Levelling/shaping of Wasteland / Fallow land for Individuals',
    'Along the coast Line Plantation of Farm Forestry Trees for Individuals',
    'Along the coast Line Plantation of Forestry Trees for Individuals',
    'Along the coast Line Plantation of Horticulture Trees for Individuals',
    'Block Plantation of Biodrainage Trees in Fields for Individuals',
    'Block Plantation of Horticulture Trees in fields for Individuals',
    'Block Plantation of Sericulture Trees in fields for Individuals',
    'Boundary Block Plantation of Coastal Shelter Belt Trees for Individuals',
    'Boundary Line Plantation of Farm Forestry Trees for Individuals',
    'Boundary Line Plantation of Forestry Trees for Individuals',
    'Boundary Line Plantation of Horticulture Trees for Individuals',
    'Development of Silvipasture Grassslands for Individuals',
    'Line Plantation of Coastal Shelter Belt Trees for Individuals',
    'Line Plantation of Shelter Belt Trees for Individuals',
    'Raising of Nursery for Individuals',
    'Wasteland Block Plantation of Biodrainage Trees for Individuals',
    'Wasteland Block Plantation of Horticulture Trees for Individuals',
    'Wasteland Line Plantation of Farm Forestry Trees for Individuals',
    'Wasteland Line Plantation of Forestry Trees for Individuals',
    'Wastelands Block Plantation of Farm Forestry Trees for Individuals',
    'Wastelands Block Plantation of Forestry Trees for Individuals',
    'Wastelands Block Plantation of Sericulture Trees for Individuals',
    'Construction of Staggered Trench for individual',
    'Construction of Irrigation Open Well for Community',
    'Construction of Irrigation Open Well for Groups',
    'Construction of Irrigation Open Well for Individuals',
    'Repair and maintenance of parapet & platform of Irrigation Open Well for Community',
    'Construction of Farm Ponds for Individuals',
    'Construction of Fish Drying Yards for Community',
    'Construction of Fish Drying Yards for Individual',
    'Repair and Maintenance of Fish Drying Yards for Community',
    'Construction of Fisheries Ponds for Community',
    'Construction of Infrastructure for Azola cultivation for Community',
    'Construction of Infrastructure for Azola cultivation for Individual',
    'Repair and Maintenance of Infrastructure for Azola cultivation for Community',
    'Construction of Cattle Shelter for Community',
    'Construction of Cattle Shelter for Individuals',
    'Construction of Goat Shelter for Community',
    'Construction of Goat Shelter for Individuals',
    'Construction of Piggery Shelter for Community',
    'Construction of Piggery Shelter for Individuals',
    'Construction of Poultry Livestock_Shelter for Individuals',
    'Construction of Poultry Shelter for Community',
    'Repair and maintenance of Cattle Shelter for Community',
    'Repair and maintenance of Goat Shelter for Community',
    'Repair and maintenance of Piggery Shelter for Community',
    'Repair and maintenance of Poultry Shelter for Community',
    'Construction of workshed for Livelihood activity for Groups',
    'Construction of Agricultural produce storage Building for Groups',
    'Construction of Infrastructure for Liquid Biomanure for Groups',
    'Construction of Anganwadi Building for Community',
    'Repair and Maintenance of Anganwadi Building for Community',
    'Construction of Crematorium for Community',
    'Repair and Maintenance of Crematorium',
    'Construction of Cyclone shelter for Community',
    'Repair and Maintenance of Cyclone shelter for Community',
    'Construction of Gram Panchayat/Panchayat Bhavan Building for Community',
    'Repair and Maintenance of Bharat Nirman Seva Kendra Building for Community',
    'Repair and Maintenance of Gram Panchayat/Panchayat Bhavan Building for Community',
    'Construction of Kitchen shed Building for Community',
    'Repair and Maintenance of Kitchen shed Building for Community',
    'Construction of Village/Rural Haat for community',
    'Repair and Maintenance of Village/Rural Haat for community',
    'Construction of SHG/Federation Building for Groups',
    'Construction of Food grain Storage Building for Community',
    'Repair and Maintenance of Food grain Storage Building for Community',
    'Drainage of chaur or waterlogged areas Land for Individuals',
    'Drainage of Community Waterlogged Land',
    'Reclamation of Community Waterlogged Land',
    'Construction of Earthen Spur for Community',
    'Construction of Embankment for community',
    'Construction of Stone Spur for Community',
    'Construction of Wire crate (gabion) Spur for Community',
    'Repair and Maintenance of Earthen Spur for Community',
    'Repair and Maintenance of Stone Spur for Community',
    'Repair and Maintenance of Wire crate (gabion) Spur for Community',
    'Construction of Flood/ Diversion Channel for Community',
    'Renovation of Flood/ Diversion Channel for Community',
    'Repair and Maintenance of Flood/ Diversion Channel for Community',
    'Construction of Diversion Storm Water Drain for Community',
    'Construction of intermediate and Link Storm Water Drain for Community',
    'Construction of Storm Water drain for coastal protection for Community',
    'Repair and maintenance of coastal protection Storm Water drain for Community',
    'Repair and maintenance of Diversion Storm Water Drain for Community',
    'Repair and maintenance of intermediate and Link Storm Water Drain for Community',
    'Maintenance of bridges constructed by the Border Roads Organization',
    'Maintenance of tunnel constructed by the Border Roads Organization',
    'Production of building material for Community',
    'Construction of Bitumen Top Roads for Community',
    'Construction of Cement Concrete Roads for Community',
    'Construction of Culvert / cross drainage structues for Community',
    'Construction of Gravel Road Roads for Community',
    'Construction of Inter-locking cement block/tiles Roads for Community',
    'Construction of Kharanja (brick/stone) Roads for Community',
    'Construction of Mitti Murram Roads for Community',
    'Construction of WBM Roads for Community',
    'Repair and maintenance of Bitumen Top Roads for Community',
    'Repair and maintenance of Cement Concrete Roads for Community',
    'Repair and Maintenance of Culvert / cross drainage structues for Community',
    'Repair and maintenance of Gravel Road Roads for Community',
    'Repair and maintenance of Inter-locking cement block/tiles Roads for Community',
    'Repair and maintenance of Kharanja (brick/stone) Roads for Community',
    'Repair and maintenance of Mitti Murram Roads for Community',
    'Repair and maintenance of WBM Roads for Community',
    'Construction of Infrastructure for Liquid Biomanure for Community',
    'Construction of Infrastructure for Liquid Biomanure for Individuals',
    'Repair and Maintenance of Infrastructure for Liquid Biomanure for Community',
    'Construction of Soak Pit for Community',
    'Construction of Soak Pit for Individual',
    'Construction of Berkeley Compost Pit for Community',
    'Construction of Berkeley Compost Pit for Groups',
    'Construction of Berkeley Compost Pit for Individual',
    'Construction of Compost Pit for Groups',
    'Construction of Compost Pit for Individual',
    'Construction of Compost Pit structure for Community',
    'Construction of Liquid Waste Chamber for Individual',
    'Construction of NADEP Compost structure for Community',
    'Construction of NADEP Compost structure for Groups',
    'Construction of NADEP Compost structure for Individual',
    'Construction of Open / Covered Grey Water/Storm Drain for Community',
    'Construction of Soakage Channel for Community',
    'Construction of Stabilization Pond for Community',
    'Construction of Vermi Compost structure for Community',
    'Construction of Vermi Compost structure for Groups',
    'Construction of Vermi Compost structure for Individual',
    'Repair and Maintenance of Berkeley Compost Pit for Community',
    'Repair and Maintenance of Compost Pit for Community',
    'Repair and Maintenance of NADEP Compost structure for Community',
    'Repair and maintenance of Open / Covered Grey Water/Storm Drain for Community',
    'Repair and maintenance of Stabilization Pond for Community',
    'Repair and Maintenance of Vermi Compost structure for Community',
    'Construction of Anganwadi Multi Unit Toilets for Community',
    'Construction of Community Sanitary Complex',
    'Construction of Multi Unit Toilets for School',
    'Construction of Single Unit Toilets for Individual',
    'Construction of Compound wall for government schools for Community',
    'Repair and Maintenance of Compound wall for government run schools for Community',
    'Construction of Play field for Community',
    'Repair and Maintenance of Play field for Community']
    return render_template("dashboard/activity_identification.html", gaw=gaw, categories=categories,
                           assets=assets,land_types=location_specific, work_types=work_types, clusters=clusters, ridges=ridges,
                           beneficiaries=beneficiaries, activities= activities, slopes=slopes, water_works=water_works,
                           major_scheduled_category=major_scheduled_category, permissible_works=permissible_works)

