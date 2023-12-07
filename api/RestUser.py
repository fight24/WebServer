# routes.py
from flask import request, jsonify, Blueprint
from Models import db, User,Token
from flask_bcrypt import Bcrypt


users_bp = Blueprint('users_bp', __name__,url_prefix='/api')
bcrypt = Bcrypt()

# Khóa (API key) để xác thực


# Middleware để kiểm tra khóa API trước khi xử lý bất kỳ yêu cầu nào trong module




@users_bp.route('/user',methods=['GET'])
def get_all_users():
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email': user.email,'password':mask_string(user.password),'img_user':user.img_user} for user in users]
    return jsonify(user_list), 200
@users_bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data['username']
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'message': 'User exist'}), 404
    email = data['email']
    password = data['password']
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password= hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@users_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    user_data = {'id': user.id, 'username': user.username, 'email': user.email,'password':mask_string(user.password),'img_user':user.img_user}
    return jsonify(user_data), 200

@users_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.username = data['username']
    user.email = data['email']
    user.password = data['password']
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200
@users_bp.route('/user/<int:user_id>/image', methods=['PUT'])
def update_img_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.img_user = data['img_user']
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200
@users_bp.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 204

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = Token.query.filter_by(user_id=user.id).first()
        if token:
            # Xóa token
            db.session.delete(token)
            db.session.commit()
        token = Token(user=user, token_value=data['token'])
        db.session.add(token)
        db.session.commit()
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Login failed'}), 401
@users_bp.route('/login-with-token/<string:token_name>',  methods=['GET'])
def login_with_token(token_name):
    token = Token.query.filter_by(token_value=token_name).first()
    
    if token:
        user = User.query.get(token.user_id)
        user_data = {'id': token.id, 'user_id': token.user_id,'user_name':user.username}
        return jsonify(user_data), 200
    else:
        return jsonify({'message': 'token or user not found'}), 404
@users_bp.route('/delete-token-by-id/<int:user_id>', methods=['DELETE'])
def delete_token_by_id_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404

    token = Token.query.filter_by(user_id=user.id).first()
    if token:
        # Xóa token
        db.session.delete(token)
        db.session.commit()
        return jsonify({'message': 'Delete successful'}), 200
    else:
        return jsonify({'message': 'Token not found'}), 404
@users_bp.route('/delete-token-by-name/<string:user_name>', methods=['DELETE'])
def delete_token_by_username(user_name):
    user = User.query.filter_by(username=user_name).first()
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    token = Token.query.filter_by(user_id=user.id).first()
    if token:
        # Xóa token
        db.session.delete(token)
        db.session.commit()
        return jsonify({'message': 'Token successful'}), 200
    else:
        return jsonify({'message': 'Token not found'}), 404
# @users_bp.route('/delete-token/<string:user_name>',  methods=['DELETE'])
# def delete_token_by_user_name(user_name):
#     user = User.query.filter_by(username=user_name).first()

#     token = Token.query.filter_by(user_id=user.id).first()
#     if token:
#     # Xóa token
#         db.session.delete(token)
#         db.session.commit()
     
#         return jsonify({'message': 'delete successful'}), 200
#     else:
    
#         return jsonify({'message': 'token not found'}), 404
@users_bp.route('/user/search/<string:username>',methods=['GET'])
def search_user_by_name(username):
    users = User.query.all()
    user_list = [{'id': user.id, 'username': user.username, 'email':user.email,'password':mask_string(user.password)} for user in users if user.username == username]
    if not user_list :
        return jsonify({'message':'None'}),404
    else:
        return jsonify(user_list),200 
def mask_string(input_string):
    masked_string = '*' * len(input_string)
    return masked_string
