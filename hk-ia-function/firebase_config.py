"""
Firebase 配置和身份驗證工具
"""
import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from flask import request, jsonify, current_app

# Firebase 初始化
def initialize_firebase():
    """初始化 Firebase Admin SDK"""
    if not firebase_admin._apps:
        # 使用正確的專案 ID
        firebase_admin.initialize_app(options={'projectId': 'hk-insurance-crawler'})
    
    return firestore.client()

def verify_firebase_token(f):
    """Firebase token 驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 從 Authorization header 獲取 token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未提供有效的身份驗證令牌'}), 401
        
        token = auth_header.split('Bearer ')[1]
        
        try:
            # 驗證 Firebase ID token
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Token 驗證失敗: {str(e)}")
            return jsonify({'error': '身份驗證失敗'}), 401
    
    return decorated_function

def verify_admin_role(f):
    """管理員角色驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'user'):
            return jsonify({'error': '請先進行身份驗證'}), 401
        
        # 檢查是否為管理員
        custom_claims = request.user.get('firebase', {}).get('sign_in_attributes', {})
        if custom_claims.get('role') != 'admin':
            return jsonify({'error': '需要管理員權限'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_user_role(uid):
    """獲取用戶角色"""
    try:
        user = auth.get_user(uid)
        custom_claims = user.custom_claims or {}
        return custom_claims.get('role', 'user')
    except Exception as e:
        current_app.logger.error(f"獲取用戶角色失敗: {str(e)}")
        return 'user'

def set_user_role(uid, role):
    """設置用戶自定義聲明（角色）"""
    try:
        auth.set_custom_user_claims(uid, {'role': role})
        return True
    except Exception as e:
        current_app.logger.error(f"設置用戶角色失敗: {str(e)}")
        return False
