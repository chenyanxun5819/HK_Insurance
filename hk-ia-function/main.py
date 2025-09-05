from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response
from takepdf import run_crawler, query_name, get_profiles_paginated, get_stats
from user_management_firestore import UserManager
from create_admin import create_admin_if_not_exists
from firestore_aml_query import FirestoreAMLQuery
from firestore_aml_updater import get_updater
import os
import json
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# 設置 JSON 編碼，確保中文字符正確顯示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# 設置日誌以便調試
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🎉 Firestore 版本 - 自動檢測環境
USE_EMULATOR = os.environ.get('FIRESTORE_EMULATOR_HOST') is not None
print(f"🚀 初始化 Firestore 用戶管理器 ({'模擬器模式' if USE_EMULATOR else 'GCP生產模式'})...")
user_manager = UserManager(use_emulator=USE_EMULATOR)

print("🚀 初始化 Firestore AML 查詢引擎...")
aml_query = FirestoreAMLQuery(use_emulator=USE_EMULATOR)

# 確保管理員帳戶存在
create_admin_if_not_exists(user_manager)

def require_auth():
    """檢查用戶認證 - 修復版"""
    # 優先從cookie獲取token
    session_token = request.cookies.get('session_token')
    
    # 備選：從Authorization header獲取
    if not session_token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
    
    logger.info(f"Auth check - Token found: {'Yes' if session_token else 'No'}")
    
    if not session_token:
        return {'valid': False, 'message': '請先登入', 'code': 'NO_TOKEN'}
    
    try:
        auth_result = user_manager.verify_session(session_token)
        logger.info(f"Auth result: {auth_result}")
        return auth_result
    except Exception as e:
        logger.error(f"Auth verification error: {str(e)}")
        return {'valid': False, 'message': f'認證失敗: {str(e)}', 'code': 'AUTH_ERROR'}

def require_admin():
    """檢查管理員權限"""
    auth_result = require_auth()
    
    if not auth_result.get('valid'):
        return auth_result
    
    try:
        user = auth_result.get('user', {})
        user_email = user.get('email', '')
        is_admin = user.get('is_admin', False)
        
        if user_email == 'astcws@gmail.com' or is_admin:
            return auth_result
        else:
            return {'valid': False, 'message': '需要管理員權限', 'code': 'NOT_ADMIN'}
            
    except Exception as e:
        return {'valid': False, 'message': f'權限檢查失敗: {str(e)}', 'code': 'ADMIN_CHECK_ERROR'}

@app.route("/")
def home():
    """主頁 - 直接顯示查詢頁面"""
    response = make_response(render_template("query.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/register", methods=["GET", "POST"])
def register():
    """用戶註冊"""
    if request.method == "GET":
        return render_template("register.html")
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"success": False, "message": "請填寫完整資訊"}), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({"success": False, "message": "請輸入有效的 Email 地址"}), 400
        
        result = user_manager.register_user(email, password)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"註冊失敗: {str(e)}"}), 500

@app.route("/login", methods=["GET", "POST"])
def login():
    """用戶登入 - 修復版"""
    if request.method == "GET":
        return render_template("login.html")
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            return jsonify({"success": False, "message": "請填寫完整資訊"}), 400
        
        result = user_manager.login_user(email, password)
        logger.info(f"Login result: {result}")
        
        if result['success']:
            # 創建響應 - 使用 make_response 而不是 jsonify
            response = make_response(jsonify(result))
            
            # 設置cookie - 更嚴格的設置
            session_token = result['session_token']
            
            # 檢查是否為HTTPS
            is_secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
            
            response.set_cookie(
                'session_token', 
                session_token,
                max_age=7*24*60*60,  # 7天
                httponly=True,
                secure=is_secure,
                samesite='Lax',
                path='/'
            )
            
            logger.info(f"Cookie set successfully. Secure: {is_secure}")
            return response, 200
        else:
            logger.warning(f"Login failed: {result.get('message')}")
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({"success": False, "message": f"登入失敗: {str(e)}"}), 500

@app.route("/logout", methods=["POST"])
def logout():
    """用戶登出"""
    try:
        session_token = request.cookies.get('session_token')
        if session_token:
            user_manager.logout_user(session_token)
        
        response = make_response(jsonify({"success": True, "message": "登出成功"}))
        response.set_cookie('session_token', '', expires=0, path='/')
        return response, 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"success": False, "message": f"登出失敗: {str(e)}"}), 500

@app.route("/profile", methods=["GET"])
def profile():
    """獲取用戶個人資料 - 修復版"""
    auth_result = require_auth()
    logger.info(f"Profile request auth result: {auth_result}")
    
    if not auth_result.get('valid', False):
        return jsonify(auth_result), 401
    
    try:
        user = auth_result.get('user', {})
        return jsonify({
            "success": True,
            "user": {
                "email": user.get('email', ''),
                "is_admin": user.get('is_admin', False),
                "membership_level": user.get('membership_level', 'basic')
            }
        }), 200
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"success": False, "message": f"獲取用戶資料失敗: {str(e)}"}), 500

@app.route("/query", methods=["GET"])
def query():
    """AML 查詢功能 - 無需認證"""
    # 正確處理 URL 編碼的參數
    try:
        name = request.args.get("name", '').strip()
        if not name:
            return jsonify({"error": "缺少 name 參數"}), 400
        
        # 確保正確解碼 UTF-8 字符
        try:
            name = name.encode('latin1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # 如果解碼失敗，保持原始字符串
            pass
            
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
    except Exception as e:
        return jsonify({"error": f"參數處理失敗: {str(e)}"}), 400
    
    try:
        # 🔥 使用 Firestore AML 查詢引擎
        result = aml_query.search_by_name(name, page, per_page)
        
        # 確保響應使用正確的 Content-Type 和編碼
        response = make_response(jsonify(result))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 200
            
    except Exception as e:
        error_response = make_response(jsonify({"error": f"查詢失敗: {str(e)}"}))
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route("/stats", methods=["GET"])
def get_stats():
    """獲取 AML 統計資訊 - 無需認證"""
    try:
        # 🔥 使用 Firestore AML 查詢引擎獲取統計
        result = aml_query.get_stats()
        return jsonify(result), 200
            
    except Exception as e:
        return jsonify({
            "error": f"獲取統計失敗: {str(e)}",
            "total_profiles": 0,
            "year_stats": []
        }), 500

@app.route("/update", methods=["GET", "POST"])
def update():
    """更新 AML 制裁名單資料 - 無需認證"""
    try:
        print("🚀 開始更新 AML 制裁名單資料...")
        
        # 🔥 使用 Firestore 版本的資料更新器 - 自動檢測環境
        updater = get_updater(use_emulator=USE_EMULATOR)
        
        # 獲取可選的年份參數
        year = request.args.get('year', type=int)
        if year:
            print(f"📅 指定更新年份: {year}")
        
        # 執行更新
        result = updater.update_aml_data(year=year)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"更新失敗: {str(e)}",
            "processed_files": 0,
            "new_records": 0
        }), 500

@app.route("/profiles", methods=["GET"])
def get_profiles():
    """分頁獲取 AML 制裁名單資料 - 無需認證"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        nationality = request.args.get('nationality', '').strip()
        
        # 🔥 使用 Firestore AML 查詢引擎
        result = aml_query.get_profiles_paginated(page, per_page, nationality)
        
        # 確保響應使用正確的 Content-Type 和編碼
        response = make_response(jsonify(result))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 200
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"獲取資料失敗: {str(e)}",
            "profiles": [],
            "total_profiles": 0
        }
        error_response = make_response(jsonify(error_result))
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

@app.route("/admin", methods=["GET"])
def admin_panel():
    """管理員面板"""
    admin_check = require_admin()
    if not admin_check.get('valid'):
        return redirect("/login")
    
    return render_template("admin.html")

@app.route("/admin/users", methods=["GET"])
def admin_get_users():
    """獲取所有用戶列表（管理員功能）"""
    admin_check = require_admin()
    if not admin_check.get('valid'):
        return jsonify(admin_check), 403
    
    result = user_manager.get_all_users()
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

if __name__ == "__main__":
    print("🎉 Firestore 版本啟動完成!")
    app.run(host="0.0.0.0", port=8000, debug=False)
