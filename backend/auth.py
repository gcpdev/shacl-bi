import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

def encode_auth_token(user_id):
    """Generates the Auth Token."""
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_auth_token(auth_token):
    """Decodes the auth token."""
    try:
        payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'), algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            user_id = decode_auth_token(token)
            if user_id in ['Signature expired. Please log in again.', 'Invalid token. Please log in again.']:
                return jsonify({'message': user_id}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(user_id, *args, **kwargs)

    return decorated
