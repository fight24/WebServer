from flask import request, jsonify, Blueprint
from Models import db, Device

devices_bp = Blueprint('devices_bp', __name__,url_prefix='/api')



# Middleware để kiểm tra khóa API trước khi xử lý bất kỳ yêu cầu nào trong module



@devices_bp.route('/device',methods=['GET'])
def get_all_devices():
    devices = Device.query.all()
    device_list = [{'id': device.id, 'name': device.name, 'code': device.code, 'type': device.type,'is_warning': device.is_warning,'image_name':device.image_name,'is_status':device.is_status} for device in devices]
    return jsonify(device_list), 200
@devices_bp.route('/device', methods=['POST'])
def create_devices():
    data = request.get_json()
    name = data['name']
    code = data['code']
    type = data['type']
    is_warning = data['is_warning']
    # image_name = data['image_name']
    is_status = data['is_status']
    new_device = Device(name=name, code=code,type=type,is_warning = is_warning,is_status=is_status)
    db.session.add(new_device)
    db.session.commit()
    return jsonify({'message': 'Device created successfully'}), 201
@devices_bp.route('/device/<int:device_id>', methods=['GET'])
def get_deivce(device_id):
    device = Device.query.get_or_404(device_id)
    device_data = {'id': device.id, 'name': device.name, 'code': device.code, 'type': device.type,'is_warning': device.is_warning,'image_name':device.image_name,'is_status':device.is_status}
    return jsonify(device_data), 200
@devices_bp.route('/device/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    device.is_warning = data['is_warning']
    device.image_name = data['image_name']
    device.name = data['name']
    device.code = data['code']
    device.type = data['type']
    device.is_status = data['is_status']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/info', methods=['PUT'])
def update_device_info(device_id):
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    device.name = data['name']
    device.type = data['type']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/image', methods=['PUT'])
def update_image_device(device_id):
    device = Device.query.get_or_404(device_id)
    if not device:
        return jsonify({'message': 'device none'}), 404
    data = request.get_json()
    device.image_name = data['image_name']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/distance', methods=['PUT'])
def update_distance_device(device_id):
    device = Device.query.get_or_404(device_id)
    if not device:
        return jsonify({'message': 'device none'}), 404

    data = request.get_json()
    device.is_warning = data['is_warning']
    device.distance = data['distance']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/warning_distance', methods=['PUT'])
def update_warning_distance_device(device_id):
    device = Device.query.get_or_404(device_id)
    if not device:
        return jsonify({'message': 'device none'}), 404
    data = request.get_json()
    device.distance = data['distance']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/warning', methods=['PUT'])
def update_warning_device(device_id):
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    device.is_warning = data['is_warning']
    db.session.commit()
    return jsonify({'message': 'device updated successfully'}), 200
@devices_bp.route('/device/<int:device_id>/status')
def update_status(device_id):
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    device.is_status = data['is_status']
    db.session.commit()
    return jsonify({'message':'device update successfully '}),200
@devices_bp.route('/device/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({'message': 'device deleted successfully'}), 204

@devices_bp.route('/device/search/<string:code>',methods=['GET'])
def search_device_by_name(code):
    devices = Device.query.all()
    device_list = [{'id': device.id, 'name': device.name, 
                    'code':device.code,'type':device.type,
                    'image_name':device.image_name} for device in devices if device.code == code]
    if not device_list :
        return jsonify({'message':'None'}),404
    else:
        return jsonify(device_list)
