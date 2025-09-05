"""
基於 Firebase Authentication 的 HK Insurance AML 查詢系統
完全重構版本 - 使用 Firebase Auth 進行身份驗證
"""
from flask import Flask, request, jsonify, render_template, make_response
from takepdf import query_name, get_profiles_paginated, get_stats
from firestore_aml_query import FirestoreAMLQuery
from firebase_config import initialize_firebase, verify_firebase_token, verify_admin_role, get_user_role, set_user_role
import os
import json
import logging

app = Flask(__name__)

# 設置 JSON 編碼，確保中文字符正確顯示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🎉 初始化 Firebase 和 Firestore
print("🚀 初始化 Firebase Authentication...")
db = initialize_firebase()

# 🚀 初始化 Firestore AML 查詢引擎
USE_EMULATOR = os.environ.get('FIRESTORE_EMULATOR_HOST') is not None
print(f"🚀 初始化 Firestore AML 查詢引擎 ({'模擬器模式' if USE_EMULATOR else 'GCP生產模式'})...")
aml_query = FirestoreAMLQuery(use_emulator=USE_EMULATOR)

@app.route("/")
def home():
    """主頁 - 無快取，確保新用戶看到正確內容"""
    response = make_response(render_template("query.html"))
    
    # 🔥 添加強制無快取標頭
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    
    return response

@app.route("/login")
def login_page():
    """登入頁面"""
    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/register")
def register_page():
    """註冊頁面"""
    response = make_response(render_template("register.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/admin")
@verify_firebase_token
@verify_admin_role
def admin_page():
    """管理員頁面"""
    response = make_response(render_template("admin.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

# ==================== API 端點 ====================

@app.route("/api/auth/status", methods=["GET"])
@verify_firebase_token
def auth_status():
    """檢查身份驗證狀態"""
    try:
        user_info = {
            'uid': request.user.get('uid'),
            'email': request.user.get('email'),
            'role': get_user_role(request.user.get('uid')),
            'email_verified': request.user.get('email_verified', False)
        }
        return jsonify({
            'authenticated': True,
            'user': user_info
        })
    except Exception as e:
        logger.error(f"獲取用戶狀態失敗: {str(e)}")
        return jsonify({'error': '獲取用戶狀態失敗'}), 500

@app.route("/api/user/profile", methods=["GET"])
@verify_firebase_token
def get_user_profile():
    """獲取用戶個人資料"""
    try:
        uid = request.user.get('uid')
        
        # 從 Firestore 獲取用戶資料
        user_doc = db.collection('users').document(uid).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['uid'] = uid
            user_data['role'] = get_user_role(uid)
            return jsonify(user_data)
        else:
            # 用戶文檔不存在，創建基本資料
            basic_profile = {
                'email': request.user.get('email'),
                'created_at': request.user.get('auth_time'),
                'email_verified': request.user.get('email_verified', False),
                'role': 'user'
            }
            
            # 保存到 Firestore
            db.collection('users').document(uid).set(basic_profile)
            
            basic_profile['uid'] = uid
            return jsonify(basic_profile)
            
    except Exception as e:
        logger.error(f"獲取用戶資料失敗: {str(e)}")
        return jsonify({'error': '獲取用戶資料失敗'}), 500

@app.route("/api/user/profile", methods=["PUT"])
@verify_firebase_token
def update_user_profile():
    """更新用戶個人資料"""
    try:
        uid = request.user.get('uid')
        data = request.get_json()
        
        # 過濾允許更新的欄位
        allowed_fields = ['display_name', 'phone', 'company', 'department']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # 更新 Firestore
        db.collection('users').document(uid).update(update_data)
        
        return jsonify({'message': '個人資料更新成功'})
        
    except Exception as e:
        logger.error(f"更新用戶資料失敗: {str(e)}")
        return jsonify({'error': '更新用戶資料失敗'}), 500

@app.route("/api/admin/users", methods=["GET"])
@verify_firebase_token
@verify_admin_role
def list_users():
    """管理員：獲取用戶列表"""
    try:
        page_token = request.args.get('page_token')
        max_results = int(request.args.get('max_results', 50))
        
        from firebase_admin import auth
        
        # 列出用戶
        page = auth.list_users(page_token=page_token, max_results=max_results)
        
        users = []
        for user in page.users:
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'creation_time': user.user_metadata.creation_timestamp.isoformat() if user.user_metadata.creation_timestamp else None,
                'last_sign_in': user.user_metadata.last_sign_in_timestamp.isoformat() if user.user_metadata.last_sign_in_timestamp else None,
                'role': get_user_role(user.uid)
            }
            users.append(user_data)
        
        return jsonify({
            'users': users,
            'next_page_token': page.next_page_token
        })
        
    except Exception as e:
        logger.error(f"獲取用戶列表失敗: {str(e)}")
        return jsonify({'error': '獲取用戶列表失敗'}), 500

@app.route("/api/admin/users/<uid>/role", methods=["PUT"])
@verify_firebase_token
@verify_admin_role
def update_user_role(uid):
    """管理員：更新用戶角色"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({'error': '無效的角色'}), 400
        
        if set_user_role(uid, new_role):
            return jsonify({'message': f'用戶角色已更新為 {new_role}'})
        else:
            return jsonify({'error': '角色更新失敗'}), 500
            
    except Exception as e:
        logger.error(f"更新用戶角色失敗: {str(e)}")
        return jsonify({'error': '更新用戶角色失敗'}), 500

# ==================== AML 查詢 API ====================

@app.route("/query_name", methods=["POST"])
@verify_firebase_token
def query_name_api():
    """AML 查詢 API - 需要身份驗證"""
    try:
        data = request.get_json()
        name_input = data.get('name', '').strip()
        
        if not name_input:
            return jsonify({'error': '請輸入查詢名稱'}), 400
        
        # 記錄查詢活動
        uid = request.user.get('uid')
        logger.info(f"用戶 {uid} 查詢: {name_input}")
        
        results = aml_query.query_name(name_input)
        
        return jsonify({
            'query': name_input,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"查詢失敗: {str(e)}")
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500

@app.route("/get_profiles", methods=["GET"])
@verify_firebase_token  
def get_profiles():
    """獲取 AML 資料 - 需要身份驗證"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        results = aml_query.get_profiles_paginated(page=page, per_page=per_page)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"獲取資料失敗: {str(e)}")
        return jsonify({'error': f'獲取資料失敗: {str(e)}'}), 500

@app.route("/get_stats", methods=["GET"])
def get_stats_public():
    """獲取統計資料 - 公開端點"""
    try:
        stats = aml_query.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"獲取統計失敗: {str(e)}")
        return jsonify({'error': f'獲取統計失敗: {str(e)}'}), 500

# ==================== 管理員功能 ====================

@app.route("/api/admin/stats", methods=["GET"])
@verify_firebase_token
@verify_admin_role
def admin_stats():
    """管理員：系統統計"""
    try:
        # AML 資料統計
        aml_stats = aml_query.get_stats()
        
        # 用戶統計（簡化版，避免過多 API 調用）
        user_stats = {
            'total_users': '需要實現',
            'active_users': '需要實現'
        }
        
        return jsonify({
            'aml_stats': aml_stats,
            'user_stats': user_stats
        })
        
    except Exception as e:
        logger.error(f"獲取管理員統計失敗: {str(e)}")
        return jsonify({'error': '獲取統計失敗'}), 500

# ==================== 錯誤處理 ====================

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': '未授權訪問'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': '訪問被拒絕'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '資源不存在'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '內部伺服器錯誤'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 啟動 Firebase Auth AML 查詢系統於 http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
