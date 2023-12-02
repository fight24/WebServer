from flask import request, jsonify, Blueprint
from Models import db, Device,User
from RestDevice import search_device_by_name
relationShip_bp = Blueprint('relationShip_bp', __name__,url_prefix='/api')
# Khóa (API key) để xác thực


# Middleware để kiểm tra khóa API trước khi xử lý bất kỳ yêu cầu nào trong module




# 1 user chua nhieu device
@relationShip_bp.route('/users/<int:user_id>/devices', methods=['GET'])
def get_user_devices(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    
    devices = user.devices
    device_list = [{'id': device.id, 'name': device.name,'code': device.code,'type': device.type,'is_warning': device.is_warning,'is_status':device.is_status,'image_name':device.image_name} for device in devices]

    return jsonify(device_list)
@relationShip_bp.route('/user/<string:username>/devices', methods=['GET'])
def get_user_devices_by_name(username):
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email':user.email,'password':mask_string(user.password),'img_user':user.img_user} for user in users if user.username == username]
    if not user_list :
        return jsonify({'message':'None'}),404
    user = user_list[0]
    # Truy cập các trường thông tin trong từ điển
    user_id = user['id']
    return get_user_devices(user_id)
    # else:
    #     devices = user.devices
    #     device_list = [{'id': device.id, 'name': device.name,'code': device.code,'type': device.type,'is_warning': device.is_warning,'image_name':device.image_name} for device in devices]
    #     return jsonify(device_list),200
def mask_string(input_string):
    masked_string = '*' * len(input_string)
    return masked_string
    
# 1 device chua nhieu user
@relationShip_bp.route('/devices/<int:device_id>/users', methods=['GET'])
def get_users_for_device(device_id):
    device = Device.query.get(device_id)
    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    users = device.users
    user_list = [{'id': user.id, 'username': user.username} for user in users]

    return jsonify(user_list)

#lay all user 
@relationShip_bp.route('/users-with-devices', methods=['GET'])
def get_users_with_devices():
    users = User.query.all()
    result = []

    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'devices': []
        }

        for device in user.devices:
            user_data['devices'].append({
                'id': device.id,
                'name': device.name,
                'code': device.code,
                'type':  device.type,
                'is_warning':  device.is_warning,
                'image_name':device.image_name,
                'is_status':device.is_status
                
            })

        result.append(user_data)

    return jsonify(result)

# add device to user
@relationShip_bp.route('/add-device-to-user/<int:user_id>', methods=['POST'])
def add_device_to_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    device_id = request.json.get('id')
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    user.devices.append(device)
    db.session.commit()

    return jsonify({'message': 'Device added to user successfully'}), 200

@relationShip_bp.route('/add-device-to-user/<string:username>',methods=['POST'])
def add_device_to_user_by_name(username):
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email':user.email,'password':mask_string(user.password),'img_user':user.img_user} for user in users if user.username == username]
    if not user_list :
        return jsonify({'message':'None'}),404
    user = user_list[0]
    # Truy cập các trường thông tin trong từ điển
    user_id = user['id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    device_code = request.json.get('code')
    devices = Device.query.all()
    device_list = [{'id': device.id, 'name': device.name, 'code':device.code,'type':device.type,'image_name':device.image_name} for device in devices if device.code == device_code]
    if not device_list :
        return jsonify({'message':'None'}),404
    device = device_list[0]
    device_id = device['id']
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    user.devices.append(device)
    db.session.commit()
    return jsonify({'message': 'Device added to user successfully'}), 200
    
#add user to device
@relationShip_bp.route('/add-user-to-device/<int:device_id>', methods=['POST'])
def add_user_to_device(device_id):
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    user_id = request.json.get('user_id')
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    device.users.append(user)
    db.session.commit()

    return jsonify({'message': 'User added to device successfully'}), 200

# remove-user-from-device
@relationShip_bp.route('/remove-user-from-device/<int:device_id>', methods=['DELETE'])
def remove_user_from_device(device_id):
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    user_id = request.json.get('user_id')
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    if user in device.users:
        device.users.remove(user)
        db.session.commit()
        return jsonify({'message': 'User removed from device successfully'}), 200
    else:
        return jsonify({'message': 'User is not associated with this device'}), 400


@relationShip_bp.route('/remove-device-from-user/<int:user_id>', methods=['DELETE'])
def remove_device_from_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    device_id = request.json.get('device_id')
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    if user in device.users:
        device.users.remove(user)
        db.session.commit()
        return jsonify({'message': 'Device removed from user successfully'}), 200
    else:
        return jsonify({'message': 'Device is not associated with this user'}), 400


@relationShip_bp.route('/remove-device-from-user/<string:username>', methods=['DELETE'])
def remove_device_from_user_by_name(username):
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email':user.email,'password':mask_string(user.password),'img_user':user.img_user} for user in users if user.username == username]
    if not user_list :
        return jsonify({'message':'None'}),404
    user = user_list[0]
    # Truy cập các trường thông tin trong từ điển
    user_id = user['id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    device_code = request.json.get('code')
    devices = Device.query.all()
    device_list = [{'id': device.id, 'name': device.name, 'code':device.code,'type':device.type,'image_name':device.image_name} for device in devices if device.code == device_code]
    if not device_list :
        return jsonify({'message':'None'}),404
    device = device_list[0]
    device_id = device['id']
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    if user in device.users:
        device.users.remove(user)
        db.session.commit()
        return jsonify({'message': 'Device removed from user successfully'}), 200
    else:
        return jsonify({'message': 'Device is not associated with this user'}), 400


@relationShip_bp.route('/remove-device-from-user/<string:username>/<string:device_code>', methods=['DELETE'])
def remove_device_from_user_by_code(username,device_code):
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email':user.email,'password':mask_string(user.password),'img_user':user.img_user} for user in users if user.username == username]
    if not user_list :
        return jsonify({'message':'None'}),404
    user = user_list[0]
    # Truy cập các trường thông tin trong từ điển
    user_id = user['id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    devices = Device.query.all()
    device_list = [{'id': device.id, 'name': device.name, 'code':device.code,'type':device.type,'image_name':device.image_name} for device in devices if device.code == device_code]
    if not device_list :
        return jsonify({'message':'None'}),404
    device = device_list[0]
    device_id = device['id']
    device = Device.query.get(device_id)

    if device is None:
        return jsonify({'message': 'Device not found'}), 404

    if user in device.users:
        device.users.remove(user)
        db.session.commit()
        return jsonify({'message': 'Device removed from user successfully'}), 200
    else:
        return jsonify({'message': 'Device is not associated with this user'}), 400
