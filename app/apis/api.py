from flask import Blueprint, current_app, jsonify, request, session
from app.models import State_UT,District,Block

blp = Blueprint('api', __name__, url_prefix='/api')

@blp.route("/states", methods=['GET'])
def states():
    states = State_UT.query.all()
    state_list = [{"id": d.id, "name": d.name} for d in states]

    return jsonify(state_list), 200

@blp.route("/districts")
def districts():
    state_id = request.args.get("state_id", type=int)

    if not state_id:
        return jsonify({"error": "state_id is required"}), 400

    districts = District.query.filter_by(state_id=state_id).all()
    district_list = [{"id": d.id, "name": d.name} for d in districts]

    return jsonify(district_list), 200

@blp.route("/blocks")
def blocks():
    district_id = request.args.get("district_id", type=int)

    if not district_id:
        return jsonify({"error": "district_id is required"}), 400

    blocks = Block.query.filter_by(district_id=district_id).all()
    block_list = [{"id": b.id, "name": b.name} for b in blocks]

    return jsonify(block_list), 200

@blp.route('/decrypt_keys')
def decrypt_keys():
    # get your keys from wherever you store them
    public_key = current_app.config.get('PUBLIC_KEY')
    return jsonify({'publicKey': public_key}), 200

