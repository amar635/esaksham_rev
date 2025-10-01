from collections import defaultdict
from datetime import datetime
from flask import Blueprint, json, jsonify, render_template, request

from app.models.user import User
from app.models.user_courses import UserCourse


blp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@blp.route('/')
def universal_dashboard():
    return render_template("dashboard/universal_dashboard.html")

@blp.route('/charts')
def charts():
    print('chart_dashboard preparing on:', datetime.now())
    total_users = User.get_total_users()
    certified_users = UserCourse.get_certified_users()
    issuance_percentage = (certified_users / total_users * 100) if total_users > 0 else 0
    card_data = {
        'total_users': total_users,
        'certified_users': certified_users,
        'issuance_percentage': f"{issuance_percentage:.2f}"
    }
    
    pie_chart_data = {
        'issued_total': certified_users,
        'non_issued_total': total_users - certified_users
    }
    
    # Fetch hierarchical data in batches
    states = UserCourse.get_state_wise_users(top_5=True)
    districts = UserCourse.get_all_district_wise_users([s['id'] for s in states], top_5=True)
    blocks = UserCourse.get_all_block_wise_users([d['id'] for d in districts], top_5=True)
    users = UserCourse.get_all_users_in_blocks([b['id'] for b in blocks])

    district_data = defaultdict(list)
    for d in districts:
        district_data[d['state_id']].append(d)

    block_data = defaultdict(list)
    for b in blocks:
        block_data[b['district_id']].append(b)

    users_data = defaultdict(list)
    for u in users:
        users_data[u['block_id']].append(u)

    bar_chart_data = {
        'states': states,
        'districts': dict(district_data),
        'blocks': dict(block_data),
        'users': dict(users_data),
    }
    
    # access_logger.info("Dashboard data prepared")
    print('chart_dashboard completed on:', datetime.now())
    return render_template('dashboard/charts_dashboard.html',card_data=card_data, 
                        pie_chart_data=pie_chart_data, bar_chart_data=bar_chart_data)

@blp.route('/data', methods=['post'])
def data():
    data = request.json
    total_users = User.get_total_users(state_id=data['state_id'], district_id=data['district_id'], block_id=data['block_id'])
    certified_users = UserCourse.get_certified_users(state_id=data['state_id'], district_id=data['district_id'], block_id=data['block_id'])
    issuance_percentage = (certified_users / total_users * 100) if total_users > 0 else 0
    card_data = {
        'total_users': total_users,
        'certified_users': certified_users,
        'issuance_percentage': f"{issuance_percentage:.2f}"
    }
    
    pie_chart_data = {
        'issued_total': certified_users,
        'non_issued_total': total_users - certified_users
    }
    
    return jsonify({'card_data': card_data, 'pie_chart_data': pie_chart_data}),200

@blp.route('/drill_chart')
def drill_chart():
     return render_template('dashboard/drill_chart.html')

@blp.route('/states', methods=['GET','POST'])
def get_dashboard_states():
    certificates = []
    certificates =UserCourse.get_state_count()
    return jsonify(certificates)

@blp.route('/districts', methods=['POST'])
def get_dashboard_districts():
    certificates = []
    data = json.loads(request.data)
    try:
        results =UserCourse.get_district_count(data['state_id'])
        return jsonify(results), 200
    except Exception as e:
            print(f"Error in get_districts: {str(e)}")
            return jsonify({'error': 'Failed to fetch districts data'}), 500

@blp.route('/blocks', methods=['POST'])
def get_dashboard_blocks():
    results = []
    data = json.loads(request.data)
    try:
        results =UserCourse.get_block_count(data['state_id'], data['district_id'])
        return jsonify(results), 200
    except Exception as e:
            print(f"Error in get_blocks: {str(e)}")
            return jsonify({'error': 'Failed to fetch blocks data'}), 500

@blp.route('/activity_identification', methods=['GET','POST'])
def activity_identification():
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
                           land_types=location_specific, work_types=work_types, clusters=clusters, ridges=ridges,
                           beneficiaries=beneficiaries, activities= activities, slopes=slopes, water_works=water_works,
                           major_scheduled_category=major_scheduled_category, permissible_works=permissible_works)