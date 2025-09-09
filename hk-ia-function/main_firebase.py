"""
基於 Firebase Authentication 的 HK Insurance AML 查詢系統
完全重構版本 - 使用 Firebase Auth 進行身份驗證
"""
from flask import Flask, request, jsonify, render_template, make_response, redirect, flash, url_for
from takepdf import query_name, get_profiles_paginated, get_stats
from firestore_aml_query import FirestoreAMLQuery
from firebase_config import initialize_firebase, verify_firebase_token, verify_admin_role, get_user_role, set_user_role
from user_management_firestore import UserManager
from create_admin import create_admin_if_not_exists
from sendgrid_service import sendgrid_service
import os
import json
import logging

app = Flask(__name__)

# 設置 Flask 應用程式配置
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.secret_key = 'hk-insurance-aml-secret-key-2025'  # 設置 session secret key

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

# 🚀 初始化 Firestore 會員管理系統
print(f"🚀 初始化 Firestore 會員管理系統 ({'模擬器模式' if USE_EMULATOR else 'GCP生產模式'})...")
user_manager = UserManager(use_emulator=USE_EMULATOR)

# 🔧 創建預設管理員帳戶
create_admin_if_not_exists(user_manager)

# 🔧 會話管理輔助函數
def get_current_user():
    """從 cookies 中獲取當前用戶資訊"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return None
        
        # 驗證會話token並獲取用戶資訊
        user_info = user_manager.get_user_by_session(session_token)
        if user_info and user_info['success']:
            return user_info['user']
        return None
    except Exception as e:
        logger.error(f"獲取用戶資訊錯誤: {str(e)}")
        return None

# 🔧 模板上下文處理器
@app.context_processor
def inject_user():
    """將用戶資訊注入所有模板"""
    try:
        current_user = get_current_user()
        return dict(current_user=current_user)
    except Exception as e:
        logger.error(f"inject_user 錯誤: {str(e)}")
        return dict(current_user=None)

@app.route("/")
def index():
    """主頁 - 無快取，確保新用戶看到正確內容"""
    response = make_response(render_template("index.html"))
    
    # 🔥 添加強制無快取標頭
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """登入頁面"""
    if request.method == "POST":
        # 處理登入表單提交
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            response = make_response(render_template("login.html", error="請提供 email 和密碼"))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
        
        # 使用 user_manager 進行登入驗證
        result = user_manager.login_user(email, password)
        
        if result['success']:
            # 登入成功，設置 session 並重導向到首頁
            response = make_response(redirect('/'))
            response.set_cookie('session_token', result['session_token'], httponly=True, secure=False)
            response.set_cookie('user_email', result['user']['email'], httponly=True, secure=False)
            return response
        else:
            # 登入失敗，顯示錯誤訊息
            response = make_response(render_template("login.html", error=result['message']))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
    
    # GET 請求，顯示登入頁面
    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/register", methods=["GET", "POST"])
def register():
    """註冊頁面"""
    if request.method == "POST":
        # 處理註冊表單提交
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not password:
            response = make_response(render_template("register.html", error="請提供 email 和密碼"))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
        
        if password != confirm_password:
            response = make_response(render_template("register.html", error="密碼與確認密碼不符"))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
        
        # 使用 user_manager 進行註冊（需要郵件驗證）
        result = user_manager.register_user_with_verification(email, password)
        
        if result['success']:
            # 發送驗證郵件
            verification_token = result['verification_token']
            email_result = sendgrid_service.send_verification_email(email, verification_token)
            
            if email_result['success']:
                flash("註冊成功！驗證郵件已發送到您的信箱，請點擊郵件中的連結完成驗證。", "success")
                response = make_response(render_template("login.html"))
            else:
                flash(f"註冊成功，但郵件發送失敗：{email_result['message']}", "warning")
                response = make_response(render_template("login.html"))
            
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
        else:
            # 註冊失敗，顯示錯誤訊息
            flash(result['message'], "error")
            response = make_response(render_template("register.html"))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
            response = make_response(render_template("register.html", error=result['message']))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache' 
            response.headers['Expires'] = '0'
            return response
    
    # GET 請求，顯示註冊頁面
    response = make_response(render_template("register.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/verify_email")
def verify_email():
    """郵件驗證頁面"""
    token = request.args.get('token')
    
    if not token:
        flash("無效的驗證連結", "error")
        return redirect(url_for('login'))
    
    # 進行郵件驗證
    result = user_manager.verify_email(token)
    
    if result['success']:
        flash("郵件驗證成功！您的帳戶已啟用，現在可以登入了。", "success")
    else:
        flash(f"驗證失敗：{result['message']}", "error")
    
    return redirect(url_for('login'))

@app.route("/forgot_password")
def forgot_password():
    """忘記密碼頁面"""
    response = make_response(render_template("forgot_password.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/logout")
def logout():
    """登出頁面"""
    session_token = request.cookies.get('session_token')
    
    if session_token:
        # 使用 user_manager 登出
        user_manager.logout_user(session_token)
    
    # 清除 cookies 並重定向到首頁
    response = make_response(redirect('/'))
    response.set_cookie('session_token', '', expires=0)
    response.set_cookie('user_email', '', expires=0)
    return response

@app.route("/change_password")
def change_password():
    """修改密碼頁面"""
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    response = make_response(render_template("change_password.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

# ==================== 會員系統 API ====================

@app.route("/api/login", methods=["POST"])
def api_login():
    """會員登入 API"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "請提供 email 和密碼"})
        
        result = user_manager.login_user(email, password)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"登入錯誤: {str(e)}")
        return jsonify({"success": False, "message": "登入過程發生錯誤"})

@app.route("/api/register", methods=["POST"])
def api_register():
    """會員註冊 API"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "請提供 email 和密碼"})
        
        result = user_manager.register_user(email, password)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"註冊錯誤: {str(e)}")
        return jsonify({"success": False, "message": "註冊過程發生錯誤"})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    """會員登出 API"""
    try:
        data = request.get_json()
        session_token = data.get('session_token')
        
        if session_token:
            result = user_manager.logout_user(session_token)
            return jsonify(result)
        else:
            return jsonify({"success": True, "message": "已登出"})
        
    except Exception as e:
        logger.error(f"登出錯誤: {str(e)}")
        return jsonify({"success": False, "message": "登出過程發生錯誤"})

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
def query_name_api():
    """AML 查詢 API - 需要登入並檢查查詢限制"""
    try:
        # 檢查用戶是否登入
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': '請先登入'}), 401
        
        # 檢查查詢限制
        limit_check = user_manager.check_query_limit(current_user['id'])
        if not limit_check.get('can_query', False):
            return jsonify({
                'success': False, 
                'message': f"查詢次數已用完。{limit_check.get('message', '')}"
            }), 403
        
        data = request.get_json()
        name_input = data.get('name', '').strip()
        
        if not name_input:
            return jsonify({'success': False, 'message': '請輸入查詢名稱'}), 400
        
        logger.info(f"查詢: {name_input} (用戶: {current_user['email']})")
        
        # 執行查詢
        results = aml_query.search_by_name(name_input)
        
        # 記錄查詢並扣減次數
        user_manager.log_query(current_user['id'], "name_search", name_input)
        
        # 獲取更新後的查詢限制
        updated_limit = user_manager.check_query_limit(current_user['id'])
        
        return jsonify({
            'success': True,
            'found': results.get('found', False),
            'matches': results.get('profiles', []),
            'total': results.get('total', 0),
            'page': results.get('page', 1),
            'total_pages': results.get('total_pages', 0),
            'query_info': {
                'remaining': updated_limit.get('remaining', 0),
                'used': updated_limit.get('used', 0),
                'limit': updated_limit.get('limit', 5)
            }
        })
        
    except Exception as e:
        logger.error(f"查詢失敗: {str(e)}")
        return jsonify({'success': False, 'message': f'查詢失敗: {str(e)}'}), 500

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

@app.route("/api/user/query_limit", methods=["GET"])
def get_user_query_limit():
    """獲取用戶查詢限制信息"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': '請先登入'}), 401
        
        limit_check = user_manager.check_query_limit(current_user['id'])
        
        return jsonify({
            'success': True,
            'query_info': {
                'can_query': limit_check.get('can_query', False),
                'remaining': limit_check.get('remaining', 0),
                'used': limit_check.get('used', 0),
                'limit': limit_check.get('limit', 5),
                'message': limit_check.get('message', '')
            }
        })
        
    except Exception as e:
        logger.error(f"獲取查詢限制失敗: {str(e)}")
        return jsonify({'success': False, 'message': f'獲取查詢限制失敗: {str(e)}'}), 500

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
    app.run(host="0.0.0.0", port=port, debug=False)
