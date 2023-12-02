# app.py
from flask import Flask,request,abort, jsonify
from Models import db,Device,Property,User,Token
from RestUser import users_bp,bcrypt
from RestDevice import devices_bp
from RestRelationship import relationShip_bp
from flask_mqtt import Mqtt
import threading  # Import thư viện threading
from datetime import datetime
import firebase_admin
from firebase_admin import credentials,messaging
import math
from functools import partial
import time
from schedule import every, repeat, run_pending
import schedule
import threading  # Import thư viện threading
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wemeio.db'

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

db.init_app(app)
bcrypt.init_app(app)
# Đặt sự kiện để báo hiệu thay đổi trong my_token_dict
my_dict = {}
my_dict["subscribed"] = set()
my_dict["my_check_status"] ={}
my_dict["location_device"] ={}
my_dict ["tokens"]= {}
with app.app_context():
     db.create_all()
     tokens = Token.query.all()
     devices = Device.query.all()
     for device in devices :
         my_dict["my_check_status"][device.code] = 0
     for token in tokens :
         my_dict ["tokens"][token.user_id] = token.token_value
# Path mặc định
distance_default = 100

default_path = '/api'
# Middleware để thêm path mặc định vào tất cả các yêu cầu
valid_api_key = "api_promax"
@app.before_request
def add_default_path():
    if not request.path.startswith(default_path):
        request.path = default_path + request.path
@app.before_request
def check_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key != valid_api_key:
        return jsonify({"message": "Unauthorized"}), 401

# Middleware để kiểm tra khóa API trước khi xử lý bất kỳ yêu cầu nào trong module



app.register_blueprint(users_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(relationShip_bp)


app.config['MQTT_BROKER_URL'] = 'petweioapp.online'  # Thay đổi địa chỉ và cổng của MQTT broker
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'SERVER_PRO_MAX'
# app.config['MQTT_USERNAME'] = 'nam'
# app.config['MQTT_PASSWORD'] = 'nam'
device_name_check = ''

mqtt = Mqtt()
mqtt.init_app(app)
mqtt_client=mqtt.client
mqtt_client.username_pw_set('admin24',password='admin24')
waiting_time = 5

# # Bắt đầu luồng MQTT
def mqtt_thread():
    mqtt.client.connect(mqtt.broker_url, mqtt.broker_port)
mqtt_thread = threading.Thread(target=mqtt_thread)


def save_data(device_code,topic,payload,time):
    with app.app_context():      
        device = Device.query.filter_by(code=device_code).first()
        if device is None:
            device = Device(code=device_code)
            db.session.add(device)
            db.session.commit()
        property = Property(topic=topic, message=payload, device=device,date=time)
        db.session.add(property)
        db.session.commit()
        # Lưu tin nhắn MQTT làm thuộc tính của thiết bị
# Hàm để subscribe vào tất cả các chủ đề của các thiết bị đã lưu trong cơ sở dữ liệu
def subscribe_to_all():
    if mqtt_client.is_connected():
        with app.app_context():
            # while True:
                # Truy vấn danh sách tất cả các mã thiết bị
                devices = Device.query.all()
                for device in devices:
                    if device.code not in my_dict["subscribed"]:
                        topic = f"devices/{device.code}"
                        mqtt.client.subscribe(topic)
                        mqtt.client.subscribe(f"devices-receive/{device.code}")
                        my_dict["subscribed"].add(device.code)
                tokens = Token.query.all()
                for token in tokens:
                    if token.token_value not in my_dict["subscribed"]:
                        topic = f"user/{token.token_value}"
                        mqtt.client.subscribe(topic)
                        my_dict["subscribed"].add(token.token_value)
                        my_dict ["tokens"][token.user_id] = token.token_value
                        



# Bắt sự kiện sau khi một thiết bị mới được thêm vào cơ sở dữ liệu
@db.event.listens_for(Device, 'after_insert')
def device_added(mapper, connection, target):
    print(f"New device added with code {target.code}")
    # Sau khi thêm thiết bị mới, subscribe vào chủ đề tương ứng
    topic = f"devices/{target.code}"
    if target.code not in my_dict["subscribed"]:
        mqtt.client.subscribe(f"devices-receive/{target.code}")
        mqtt.client.subscribe(topic)
        my_dict["subscribed"].add(target.code)
        

@db.event.listens_for(Device, 'after_delete')
def device_deleted(mapper, connection, target):
    print(f"Device deleted with code {target.code}")
    topic = f"devices/{target.code}"
    if target.code in my_dict["subscribed"]:
        mqtt.client.unsubscribe(f"devices-receive/{target.code}")
        mqtt.client.unsubscribe(topic)
        my_dict["subscribed"].remove(target.code)

# lang nghe su kien tu bang token
@db.event.listens_for(Token, 'after_insert')
def device_added(mapper, connection, target):
    print(f"New token added with id {target.id} with {target.user_id}")
    # Sau khi thêm thiết bị mới, subscribe vào chủ đề tương ứng
    topic = f"user/{target.token_value}"
    global my_dict

    if target.token_value not in my_dict["subscribed"]:
        mqtt.client.subscribe(topic)
        my_dict["subscribed"].add(target.token_value)
        my_dict ["tokens"][target.user_id] = target.token_value
        schedule.every(10).seconds.do(lambda: check_device_status(target.token_value)).tag(target.token_value,target.token_value)

@db.event.listens_for(Token, 'after_delete')
def device_deleted(mapper, connection, target):
    print(f"Token deleted with id {target.id}")
    topic = f"user/{target.token_value}"
    global my_dict

    if target.token_value in my_dict["subscribed"]:
        mqtt.client.unsubscribe(topic)
        my_dict["subscribed"].remove(target.token_value)
        del my_dict ["tokens"][target.user_id]
        schedule.clear(target.token_value)
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        subscribe_to_all()
    else:
        mqtt.client.reconnect()
        print(f"Connection to MQTT broker failed with code {rc}")

@mqtt.on_message()
def handle_message(client, userdata, message):
    warning_device_check =[]
    topic = message.topic
    payload = message.payload.decode('utf-8')
    # Xử lý thông điệp dựa trên chủ đề
    if "devices-receive/" in topic:
        device_code = topic.split("/")[-1]
       
        global my_dict
        # Cập nhật thời điểm nhận được tin nhắn
        my_dict["my_check_status"][device_code] = time.time()
    if "devices/" in topic:
        # Xử lý thông điệp từ thiết bị
        device_code = topic.split("/")[-1]
        my_dict["location_device"][search_name_device_by_name(device_code)] = cut_str_of_payload(payload)

    # Tìm thiết bị tương ứng hoặc tạo mới nếu chưa tồn tại
        try:
            date_time = datetime.now()
            save_data(device_code,topic,payload,date_time)
        except:
            print(f'save_data : error')
        print(f"Message from device topic '{topic}': {payload}")
    if "user/" in topic:
        user_token = topic.split("/")[-1]
        print(user_token)
        warning_device_check = search_device__by_token_warning(user_token)
        if len(warning_device_check) > 0 and warning_device_check is not None:
            my_dict["user_token"][user_token] = [cut_str_of_payload(payload),warning_device_check]
        print(f"Message from user topic '{topic}': {payload}")
    handle_notify(warning_device_check)
  
    timer = threading.Timer(360000,auto_delete_properties)
    # timer.start()

def handle_notify(warning_device_check):
      if len(warning_device_check) > 0 and warning_device_check is not None:
        # Tạo một từ điển mới để lưu trữ thông tin vị trí của từng thiết bị của mỗi người dùng
        user_location_dict = {}

        # Lặp qua từ điển my_token_dict
        for key, value in my_dict["user_token"].items():
            user_value, devices = value
            print(f"User: '{key}', User value: {user_value}")
            print(f"User: '{key}', devices: {devices}")
            # Lặp qua từng thiết bị trong set devices
            for device in devices:
                # Kiểm tra xem thiết bị có trong từ điển location_device không
                if device in my_dict["location_device"]:
                    # Lấy thông tin vị trí của thiết bị và lưu vào user_location_dict
                    user_location_dict[device] = my_dict["location_device"][device]
                    location_device=my_dict["location_device"]
                    print(f"Device: '{device}', Location: {location_device[device]}")
                    print(f" User: '{key}', User lat: {user_value[0]}, User lng: {user_value[1]}, Device: '{device}', Lat: {location_device[device][0]},Lng: {location_device[device][1]}")
                    distance = haversine(user_value[0],user_value[1],location_device[device][0],location_device[device][1])

                    print(f"distance: '{distance}' km")
                    # t = threading.Timer(waiting_time,partial(send_distance_alert,key,device,distance,1000))
                    # t.start
                    with app.app_context():
                        search_device = Device.query.filter_by(name=device).first()
                        if not search_device.is_status:
                            send_status_alert(key,device)
                        send_distance_alert(key,device,distance,search_device.distance)
                else:
                    print(f"Device: '{device}' not found in location_device dictionary")
def auto_delete_properties() :
    with app.app_context():
        try:
            num_deleted = db.session.query(Property).delete()
            db.session.commit()
            print (f'Deleted {num_deleted} properties')
        except Exception as e :
            db.session.rollback()
            print(str(e))
@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level,buf)


@app.route('/api/latest_property/<device_code>', methods=['GET'])
def get_latest_property(device_code):
    device = Device.query.filter_by(code=device_code).first()
    if device is None:
        return jsonify({'error': 'Device not found'}), 404

    latest_property = Property.query.filter_by(device=device).order_by(Property.date.desc()).first()
    if latest_property is None:
        return jsonify({'error': 'No data available for this device'}), 404

    return jsonify({
        'device_code': device_code,
        'latest_property': {
            'topic': latest_property.topic,
            'message': latest_property.message,
            'date': latest_property.date.strftime('%Y-%m-%d %H:%M:%S')
        }
    })
@app.route('/api/properties/<string:device_code>',methods=['GET'])
def search_properties_by_code(device_code):
    device = Device.query.filter_by(code = device_code).first()
    if device is None:
        return jsonify({'message': 'Device not found'}), 404
    else:
        properties = Property.query.all()
        property_list = [{'id':property.id,'topic':property.topic,'message':property.message,
                          'date':property.date.strftime('%Y-%m-%d %H:%M:%S')
                          } for property in properties if property.device_id == device.id]
        return jsonify(property_list)

@app.route('/api/properties/delete_all',methods=['DELETE'])
def delete_all_properties():
        try:
            num_deleted = db.session.query(Property).delete()
            db.session.commit()
            return f'Deleted {num_deleted} properties',200
        except Exception as e :
            db.session.rollback()
            return str(e),500

# import schedule
# import time



# def cleanup_data():
#     # Đếm số lượng hàng trong bảng YourModel
#     record_count = Property.query.count()

#     if record_count > 200:
#         # Lấy dữ liệu cần xóa (ví dụ: 50 hàng đầu tiên)
#         data_to_delete = Property.query.limit(record_count - 200).all()

#         # Xóa dữ liệu
#         for item in data_to_delete:
#             db.session.delete(item)

#         # Lưu thay đổi vào cơ sở dữ liệu
#         db.session.commit()
# # Xác định một công việc kiểm tra hàng ngày lúc 3 giờ sáng
# schedule.every().day.at("03:00").do(cleanup_data)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
def send_distance_alert(user_token,device_name, current_distance, threshold_distance):
    print('send distance alert')
    current_distance_km = round(current_distance)
    current_distance_m = round(current_distance*1000)
    print(f'current {current_distance}')
    if current_distance_m > threshold_distance:

        # Khoảng cách vượt quá ngưỡng, gửi thông báo
        message = messaging.Message(
            notification=messaging.Notification(
                title="Distance warning",
                body=f"The current distance of {device_name} is {current_distance_m} m.",
            ),
            token=user_token,
        )
        try:
            response = messaging.send(message)
            print('send_distance_alert: Successfully sent message:', response)
        except Exception as e:
            print('send_distance_alert: Error sending message:', str(e))
        time.sleep(10)

def haversine(lat1, lon1, lat2, lon2):
    # Chuyển đổi độ sang radian
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Bán kính trái đất (đơn vị: km)
    radius = 6371

    # Công thức Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = radius * c

    return distance
def cut_str_of_payload(payload):
    if payload is not None:
        if '[' and ']' in payload:
            payload = payload.replace("[", "").replace("]", "")
        if "," in payload:
            float_points = [float(x) for x in payload.split(",")]
            # Bây giờ lat và lng là số kiểu float
        if float_points is not None:
            print("Kinh độ:", float_points[0])
            print("Vĩ độ:", float_points[1])
        return float_points
def search_name_device_by_name(code):
    with app.app_context():
        name = None
        devices = Device.query.filter_by(code=code).first()
        if devices:
            if devices.is_warning:
                name = devices.name
        return name
def search_device__by_token_warning(token_value):
    with app.app_context():
        tokens = Token.query.filter_by(token_value=token_value).first()
        id_user = tokens.user_id
        print(id_user)
        user = User.query.get(id_user)
        devices = user.devices
        if user is None:
            return None
        
        warning_device_names = []
        for device in devices:
            if device.is_warning:
                warning_device_names.append(device.name)
        return warning_device_names
def search_code_device_by_token(token_value):
    with app.app_context():
        tokens = Token.query.filter_by(token_value=token_value).first()
        id_user = tokens.user_id
        print(id_user)
        user = User.query.get(id_user)
        devices = user.devices
        if user is None:
            return None
        device_codes = []
        for device in devices:
            device_codes.append(device.code)
        return device_codes
def check_device_location_status(key):
    
    current_time = time.time()
    time_since_last_message = current_time - my_dict["my_check_status"][key]
    if time_since_last_message > 20:  # Kiểm tra sau 10 giây không có tin nhắn
        with app.app_context():
            device = Device.query.filter_by(code=key).first()
            if device.is_status:
                device.is_status = False
                db.session.commit()
        print(f"{key} is not active.")       
    else:
        with app.app_context():
            device = Device.query.filter_by(code=key).first()
            if not device.is_status:
                device.is_status = True
                db.session.commit()
        print(f"{key} is active.")
def check_device_status(user_token):
    # Thực hiện kiểm tra trạng thái thiết bị ở đây
    print(f"Checking device status...")
    # TODO: Thêm mã kiểm tra trạng thái thiết bị của bạn ở đây
    device_set = search_code_device_by_token(user_token)
    if device_set is not None:
        for value in device_set:
            print(f"value: {value}")
            mqtt.client.publish(f"devices-ping/{value}",f"Hi! device {value}")
            try:
                check_device_location_status(value)
            except Exception as e:
                print(f"Error: {e}")

def check_thread(value):
    schedule.every(10).seconds.do(lambda: check_device_status(value)).tag(value,value)
def check_thead_full():
    print("check_thead_full")
    check_threads = []
    # stop_event = threading.Event()
    # Bắt đầu một luồng cho mỗi user_token
    if my_dict is not None:
        for key, value in my_dict["tokens"].items():
            check_thread(value)
    # Chờ tất cả các luồng hoàn thành
    # try:
    #     for thread in check_threads:
    #         thread.join()
    # finally:
    #     stop_event.set()
    while True:
        schedule.run_pending()
        time.sleep(1)


# Bắt đầu một luồng cho hàm lắng nghe sự kiện thay đổi trong my_token_dict
# Bắt đầu luồng chính cho hàm check_thead_full
check_full_thread = threading.Thread(target=check_thead_full)
check_thead_full.daemon = True
check_full_thread.start()
mqtt_thread.daemon = True  # Đánh dấu luồng như là một daemon (sẽ dừng khi ứng dụng Flask kết thúc)
mqtt_thread.start()

def send_status_alert(user_token,device_name):
    print('send status alert')
     # Khoảng cách vượt quá ngưỡng, gửi thông báo
    message = messaging.Message(
            notification=messaging.Notification(
                title="Distance warning",
                body=f"The  {device_name} is not active.",
            ),
            token=user_token,
        )
    try:
            response = messaging.send(message)
            print('send_distance_alert: Successfully sent message:', response)
    except Exception as e:
            print('send_distance_alert: Error sending message:', str(e))
    
    
