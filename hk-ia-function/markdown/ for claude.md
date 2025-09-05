# login.html
```
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登入 - HK Insurance AML 查詢系統</title>
    <!-- 版本: v2.3.1 - 修復 session token 編碼問題 - 2025-09-04 21:35 -->
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }

        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }

        .login-header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .login-header p {
            color: #666;
            font-size: 14px;
        }

        .admin-info {
            background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 13px;
            line-height: 1.4;
        }

        .admin-info h4 {
            margin-bottom: 8px;
            font-size: 14px;
        }

        .admin-credentials {
            background: rgba(255, 255, 255, 0.2);
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
            font-family: monospace;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .login-btn:hover {
            transform: translateY(-2px);
        }

        .login-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }

        .form-links {
            text-align: center;
            margin-top: 20px;
        }

        .form-links a {
            color: #667eea;
            text-decoration: none;
        }

        .form-links a:hover {
            text-decoration: underline;
        }

        .alert {
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            display: none;
        }

        .alert.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .alert.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
    </style>
</head>

<body>
    <div class="login-container">
        <div class="login-header">
            <h1>用戶登入</h1>
            <p>HK Insurance AML 查詢系統</p>
        </div>

        <div id="alert" class="alert"></div>

        <form id="loginForm">
            <div class="form-group">
                <label for="email">Email 地址</label>
                <input type="email" id="email" name="email" required>
            </div>

            <div class="form-group">
                <label for="password">密碼</label>
                <input type="password" id="password" name="password" required>
            </div>

            <button type="submit" class="login-btn" id="loginBtn">登入</button>
        </form>

        <div class="form-links">
            <p>還沒有帳號？ <a href="/register">立即註冊</a></p>
            <p><a href="/forgot-password">忘記密碼？</a></p>
        </div>

        <div
            style="text-align: center; margin-top: 20px; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 15px;">
            🔧 版本 v2.3.1 | 修復 session token 編碼問題<br>
            部署時間: 2025-09-04 21:35
        </div>
    </div>

    <script>
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const alert = document.getElementById('alert');

        function showAlert(message, type) {
            alert.textContent = message;
            alert.className = `alert ${type}`;
            alert.style.display = 'block';
        }

        function hideAlert() {
            alert.style.display = 'none';
        }

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();

            const formData = new FormData(loginForm);
            const email = formData.get('email');
            const password = formData.get('password');

            if (!email || !password) {
                showAlert('請填寫完整資訊', 'error');
                return;
            }

            loginBtn.disabled = true;
            loginBtn.textContent = '登入中...';

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',  // 重要：包含 cookies
                    body: JSON.stringify({ email, password })
                });

                const result = await response.json();

                if (result.success) {
                    showAlert('登入成功，正在跳轉...', 'success');
                    // 給 cookie 一點時間設定，然後跳轉
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 500);
                } else {
                    showAlert(result.message || '登入失敗', 'error');
                }
            } catch (error) {
                showAlert('登入失敗，請稍後再試', 'error');
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = '登入';
            }
        });
    </script>
</body>

</html>
```

# main.py
```
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from takepdf import run_crawler, query_name, get_profiles_paginated, get_stats
from user_management_firestore import UserManager
from create_admin import create_admin_if_not_exists
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# 🎉 Firestore 版本 - 不再需要資料庫檔案管理
print("🚀 初始化 Firestore 用戶管理器...")
user_manager = UserManager()

# 確保管理員帳戶存在
create_admin_if_not_exists(user_manager)

def require_auth():
    """檢查用戶認證"""
    session_token = request.headers.get('Authorization') or request.cookies.get('session_token')
    if not session_token:
        return {'valid': False, 'message': '請先登入'}
    
    auth_result = user_manager.verify_session(session_token)
    return auth_result

def require_admin():
    """檢查管理員權限"""
    session_token = request.headers.get('Authorization') or request.cookies.get('session_token')
    
    if not session_token:
        return {'valid': False, 'message': '請先登入'}
    
    try:
        auth_result = user_manager.verify_session(session_token)
        
        if auth_result.get('valid'):
            user = auth_result.get('user', {})
            user_email = user.get('email', '')
            is_admin = user.get('is_admin', False)
            
            if user_email == 'astcws@hotmail.com' or is_admin:
                return auth_result
            else:
                return {'valid': False, 'message': '需要管理員權限'}
        else:
            return auth_result
            
    except Exception as e:
        return {'valid': False, 'message': f'權限檢查失敗: {str(e)}'}

@app.route("/")
def home():
    auth_result = require_auth()
    if not auth_result.get('valid', False):
        return redirect('/login')
    
    return render_template("query.html")

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
    """用戶登入"""
    if request.method == "GET":
        return render_template("login.html")
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"success": False, "message": "請填寫完整資訊"}), 400
        
        result = user_manager.login_user(email, password)
        
        if result['success']:
            response = jsonify(result)
            is_secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
            response.set_cookie('session_token', result['session_token'], 
                              max_age=7*24*60*60,
                              httponly=True, 
                              secure=is_secure, 
                              samesite='Lax',
                              path='/')
            return response, 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({"success": False, "message": f"登入失敗: {str(e)}"}), 500

@app.route("/logout", methods=["POST"])
def logout():
    """用戶登出"""
    try:
        session_token = request.headers.get('Authorization') or request.cookies.get('session_token')
        if session_token:
            user_manager.logout_user(session_token)
        
        response = jsonify({"success": True, "message": "登出成功"})
        response.set_cookie('session_token', '', expires=0)
        return response, 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"登出失敗: {str(e)}"}), 500

@app.route("/profile", methods=["GET"])
def profile():
    """獲取用戶個人資料"""
    auth_result = require_auth()
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
        return jsonify({"success": False, "message": f"獲取用戶資料失敗: {str(e)}"}), 500

@app.route("/query", methods=["GET"])
def query():
    # 檢查用戶認證
    auth_result = require_auth()
    if not auth_result.get('valid', False):
        return jsonify(auth_result), 401
    
    user = auth_result['user']
    
    # 檢查查詢限制
    query_limit_check = user_manager.check_query_limit(user['id'])
    if not query_limit_check['can_query']:
        return jsonify({
            "success": False, 
            "message": f"已達到每日查詢限制 ({query_limit_check['daily_limit']} 次)",
            "query_stats": query_limit_check
        }), 429
    
    name = request.args.get("name")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    if not name:
        return jsonify({"error": "缺少 name 參數"}), 400
    
    try:
        # 記錄查詢
        user_manager.log_query(user['id'], 'name_search', json.dumps({'name': name, 'page': page}))
        
        # AML 查詢邏輯保持不變 (仍使用 SQLite)
        if os.path.exists('aml_profiles.db'):
            import sqlite3
            
            conn = sqlite3.connect('aml_profiles.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            table_name = 'aml_profiles' if 'aml_profiles' in tables else 'profiles'
            
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE LOWER(name) LIKE LOWER(?)"
            cursor.execute(count_query, [f"%{name}%"])
            total = cursor.fetchone()[0]
            
            if total == 0:
                conn.close()
                return jsonify({"found": False, "matches": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}), 200
            
            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            data_query = f"SELECT * FROM {table_name} WHERE LOWER(name) LIKE LOWER(?) LIMIT ? OFFSET ?"
            cursor.execute(data_query, [f"%{name}%", per_page, offset])
            records = cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            
            matches = []
            for record in records:
                record_dict = dict(zip(column_names, record))
                matches.append(record_dict)
            
            conn.close()
            
            return jsonify({
                "found": True,
                "matches": matches,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }), 200
        else:
            return jsonify({"error": "資料庫檔案不存在"}), 500
            
    except Exception as e:
        return jsonify({"error": f"查詢失敗: {str(e)}"}), 500

@app.route("/profiles", methods=["GET"])
def get_profiles():
    """分頁獲取 AML 制裁名單資料"""
    auth_result = require_auth()
    if not auth_result.get('valid', False):
        return jsonify(auth_result), 401
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        nationality = request.args.get('nationality', '').strip()
        
        if os.path.exists('aml_profiles.db'):
            import sqlite3
            conn = sqlite3.connect('aml_profiles.db')
            cursor = conn.cursor()
            
            # 檢查表格是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            table_name = 'aml_profiles' if 'aml_profiles' in tables else 'profiles'
            
            # 構建查詢條件
            where_conditions = []
            params = []
            
            if nationality:
                where_conditions.append("LOWER(nationality) LIKE LOWER(?)")
                params.append(f"%{nationality}%")
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 計算總數
            count_query = f"SELECT COUNT(*) FROM {table_name}{where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            if total == 0:
                conn.close()
                return jsonify({
                    "success": True,
                    "profiles": [],
                    "total_profiles": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0
                }), 200
            
            # 計算分頁
            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # 獲取資料
            data_query = f"SELECT * FROM {table_name}{where_clause} LIMIT ? OFFSET ?"
            cursor.execute(data_query, params + [per_page, offset])
            records = cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            
            profiles = []
            for record in records:
                record_dict = dict(zip(column_names, record))
                profiles.append(record_dict)
            
            conn.close()
            
            return jsonify({
                "success": True,
                "profiles": profiles,
                "total_profiles": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "資料庫檔案不存在",
                "profiles": [],
                "total_profiles": 0
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"獲取資料失敗: {str(e)}",
            "profiles": [],
            "total_profiles": 0
        }), 500

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
    app.run(host="0.0.0.0", port=8080, debug=False)

```

# query.html
```
<!doctype html>
<html lang="zh-Hant">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>反洗錢制裁名單查詢系統</title>
    <style>
        body {
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
            margin: 0;
            padding: 2rem;
            background: #f8f9fa;
        }

        .user-bar {
            background: #667eea;
            color: white;
            padding: 1rem 2rem;
            margin: -2rem -2rem 2rem -2rem;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .query-quota {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        .logout-btn,
        .admin-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }

        .logout-btn:hover,
        .admin-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .admin-btn {
            background: rgba(255, 215, 0, 0.3);
            border-color: rgba(255, 215, 0, 0.5);
        }

        .admin-btn:hover {
            background: rgba(255, 215, 0, 0.5);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 2rem;
        }

        h1 {
            color: #1a365d;
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 0.5rem;
            font-size: 1.2rem;
        }

        .data-source {
            text-align: right;
            color: #666;
            font-size: 0.9rem;
            font-style: italic;
            margin-bottom: 2rem;
        }

        .search-section {
            background: #f7fafc;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }

        .search-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .search-group {
            flex: 1;
            min-width: 200px;
        }

        label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #2d3748;
        }

        input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            font-size: 1rem;
            box-sizing: border-box;
        }

        input:focus {
            outline: none;
            border-color: #3182ce;
            box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
        }

        button {
            background: #3182ce;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            height: fit-content;
            align-self: end;
        }

        button:hover {
            background: #2c5282;
        }

        button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
        }

        .stats-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding: 1rem;
            background: #edf2f7;
            border-radius: 4px;
        }

        .stats-info {
            color: #4a5568;
            font-size: 0.9rem;
        }

        .table-container {
            overflow-x: auto;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th {
            background: #f7fafc;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #e2e8f0;
        }

        td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #e2e8f0;
        }

        tr:hover {
            background: #f7fafc;
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1.5rem;
        }

        .pagination button {
            background: #e2e8f0;
            color: #4a5568;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
        }

        .pagination button:hover:not(:disabled) {
            background: #cbd5e0;
        }

        .pagination button.active {
            background: #3182ce;
            color: white;
        }

        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }

        .success {
            background: #c6f6d5;
            color: #2d7d32;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }

        .search-result {
            background: #e6fffa;
            border: 1px solid #81e6d9;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }

        .search-result h3 {
            margin: 0 0 0.5rem 0;
            color: #234e52;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: #3182ce;
            color: white;
            border-radius: 12px;
            font-size: 0.75rem;
            margin-left: 0.5rem;
        }

        @media (max-width: 768px) {
            .search-row {
                flex-direction: column;
            }

            .stats-bar {
                flex-direction: column;
                gap: 0.5rem;
                text-align: center;
            }

            .pagination {
                flex-wrap: wrap;
            }
        }
    </style>
</head>

<body>
    <div class="container">
        <!-- 用戶狀態欄 -->
        <div class="user-bar" id="userBar" style="display: none;">
            <div class="user-info">
                <span>👤 <span id="userEmail"></span></span>
                <span class="query-quota" id="queryQuota">查詢額度: 載入中...</span>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button class="admin-btn" id="adminBtn" onclick="window.location.href='/admin'"
                    style="display: none;">👑 管理</button>
                <button class="logout-btn" onclick="showChangePasswordModal()">🔑 改密碼</button>
                <button class="logout-btn" onclick="logout()">登出</button>
            </div>
        </div>

        <h1>反洗錢制裁名單查詢系統</h1>
        <p class="data-source">資料來源：香港保險業監管局</p>

        <!-- 搜尋區域 -->
        <div class="search-section">
            <div class="search-row">
                <div class="search-group">
                    <label for="nameSearch">姓名查詢</label>
                    <input id="nameSearch" type="text" placeholder="輸入英文姓名，例如：Mohammed" />
                </div>
                <div class="search-group">
                    <label for="nationalityFilter">國籍過濾</label>
                    <input id="nationalityFilter" type="text" placeholder="輸入國籍，例如：Pakistan" />
                </div>
                <button id="searchBtn">查詢</button>
                <button id="clearBtn" style="background: #718096;">清除</button>
            </div>
            <div id="searchResult"></div>
        </div>

        <!-- 統計資訊 -->
        <div class="stats-bar">
            <div class="stats-info" id="statsInfo">載入中...</div>
            <div class="stats-info" id="pageInfo"></div>
        </div>

        <!-- 資料表格 -->
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>序號</th>
                        <th>姓名</th>
                        <th>國籍</th>
                        <th>護照號碼</th>
                        <th>年份</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr>
                        <td colspan="5" class="loading">正在載入資料...</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 分頁導航 -->
        <div class="pagination" id="pagination"></div>
    </div>

    <script>
        // 全域變數
        let currentPage = 1;
        let totalPages = 1;
        let isLoading = false;
        let currentNationality = '';
        let currentSearchName = '';
        let currentUser = null;

        // 認證相關函數
        async function checkAuth() {
            try {
                const response = await fetch('/profile', {
                    credentials: 'include'
                });
                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        currentUser = result.user;
                        updateUserBar(result.user, result.query_stats);
                        return true;
                    }
                }
            } catch (error) {
                console.error('認證檢查失敗:', error);
            }

            // 未登入，跳轉到登入頁面
            window.location.href = '/login';
            return false;
        }

        function updateUserBar(user, queryStats) {
            const userBar = document.getElementById('userBar');
            const userEmail = document.getElementById('userEmail');
            const queryQuota = document.getElementById('queryQuota');
            const adminBtn = document.getElementById('adminBtn');

            userEmail.textContent = user.email;

            if (queryStats.daily_limit === Infinity) {
                queryQuota.textContent = `查詢額度: 無限制`;
            } else {
                queryQuota.textContent = `查詢額度: ${queryStats.remaining}/${queryStats.daily_limit}`;
            }

            // 顯示管理員按鈕（如果用戶是管理員）
            if (user.is_admin) {
                adminBtn.style.display = 'block';
            } else {
                adminBtn.style.display = 'none';
            }

            userBar.style.display = 'flex';
        }

        async function logout() {
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('登出失敗:', error);
                window.location.href = '/login';
            }
        }

        function updateQueryStats(queryStats) {
            const queryQuota = document.getElementById('queryQuota');
            if (queryStats) {
                if (queryStats.daily_limit === Infinity) {
                    queryQuota.textContent = `查詢額度: 無限制`;
                } else {
                    queryQuota.textContent = `查詢額度: ${queryStats.remaining}/${queryStats.daily_limit}`;
                }
            }
        }

        // DOM 元素
        const nameSearch = document.getElementById('nameSearch');
        const nationalityFilter = document.getElementById('nationalityFilter');
        const searchBtn = document.getElementById('searchBtn');
        const clearBtn = document.getElementById('clearBtn');
        const searchResult = document.getElementById('searchResult');
        const statsInfo = document.getElementById('statsInfo');
        const pageInfo = document.getElementById('pageInfo');
        const tableBody = document.getElementById('tableBody');
        const pagination = document.getElementById('pagination');

        // 初始化
        document.addEventListener('DOMContentLoaded', async function () {
            // 首先檢查認證
            const isAuthenticated = await checkAuth();
            if (!isAuthenticated) return;

            loadStats();
            loadProfiles();

            // 事件監聽
            searchBtn.addEventListener('click', performSearch);
            clearBtn.addEventListener('click', clearFilters);

            nameSearch.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') performSearch();
            });

            nationalityFilter.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') performSearch();
            });
        });

        // 載入統計資訊
        async function loadStats() {
            try {
                const response = await fetch('/stats', {
                    credentials: 'include'
                });
                const data = await response.json();

                if (data.error) {
                    statsInfo.textContent = '統計資訊載入失敗';
                    return;
                }

                const totalText = `總計 ${data.total_profiles.toLocaleString()} 筆制裁資料`;
                const yearText = `涵蓋 ${data.year_stats.length} 個年份 (${data.year_stats[data.year_stats.length - 1]?.year}-${data.year_stats[0]?.year})`;
                statsInfo.textContent = `${totalText} • ${yearText}`;

            } catch (error) {
                console.error('載入統計失敗:', error);
                statsInfo.textContent = '統計資訊載入失敗';
            }
        }

        // 載入制裁名單
        async function loadProfiles(page = 1, nationality = '') {
            if (isLoading) return;

            isLoading = true;
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">正在載入資料...</td></tr>';

            try {
                const params = new URLSearchParams({
                    page: page,
                    nationality: nationality
                });

                const response = await fetch(`/profiles?${params}`, {
                    credentials: 'include'
                });

                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }

                if (response.status === 429) {
                    const data = await response.json();
                    showTableMessage(data.message || '已達到查詢限制', 'error');
                    updateQueryStats(data.query_stats);
                    return;
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // 更新查詢統計
                if (data.query_stats) {
                    updateQueryStats(data.query_stats);
                }

                currentPage = data.page;
                totalPages = data.total_pages;
                currentNationality = nationality;

                renderTable(data.profiles, page);
                renderPagination(data);
                updatePageInfo(data);

                // 確保分頁控制在瀏覽模式下顯示
                pagination.style.display = 'flex';

            } catch (error) {
                console.error('載入資料失敗:', error);
                tableBody.innerHTML = `<tr><td colspan="5" class="error">載入失敗: ${error.message}</td></tr>`;
            } finally {
                isLoading = false;
            }
        }

        // 渲染表格
        function renderTable(profiles, page) {
            if (profiles.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">沒有找到符合條件的資料</td></tr>';
                return;
            }

            const startIndex = (page - 1) * 20;
            tableBody.innerHTML = profiles.map((profile, index) => `
                <tr>
                    <td>${startIndex + index + 1}</td>
                    <td><strong>${escapeHtml(profile.name)}</strong></td>
                    <td>${escapeHtml(profile.nationality)} ${profile.year ? `<span class="badge">${profile.year}</span>` : ''}</td>
                    <td>${escapeHtml(profile.passport_no)}</td>
                    <td>${profile.year || '-'}</td>
                </tr>
            `).join('');
        }

        // 渲染分頁
        function renderPagination(data) {
            if (data.total_pages <= 1) {
                pagination.innerHTML = '';
                return;
            }

            let html = '';

            // 上一頁
            html += `<button ${!data.has_prev ? 'disabled' : ''} onclick="changePage(${data.page - 1})">‹ 上一頁</button>`;

            // 頁碼
            const startPage = Math.max(1, data.page - 2);
            const endPage = Math.min(data.total_pages, data.page + 2);

            if (startPage > 1) {
                html += `<button onclick="changePage(1)">1</button>`;
                if (startPage > 2) html += `<span>...</span>`;
            }

            for (let i = startPage; i <= endPage; i++) {
                html += `<button class="${i === data.page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
            }

            if (endPage < data.total_pages) {
                if (endPage < data.total_pages - 1) html += `<span>...</span>`;
                html += `<button onclick="changePage(${data.total_pages})">${data.total_pages}</button>`;
            }

            // 下一頁
            html += `<button ${!data.has_next ? 'disabled' : ''} onclick="changePage(${data.page + 1})">下一頁 ›</button>`;

            pagination.innerHTML = html;
        }

        // 更新頁面資訊
        function updatePageInfo(data) {
            const start = (data.page - 1) * data.per_page + 1;
            const end = Math.min(data.page * data.per_page, data.total);
            pageInfo.textContent = `第 ${data.page} 頁，共 ${data.total_pages} 頁 (顯示 ${start}-${end}，共 ${data.total.toLocaleString()} 筆)`;
        }

        // 換頁
        function changePage(page) {
            if (page < 1 || page > totalPages || isLoading) return;

            // 如果當前是搜尋模式，使用搜尋分頁
            if (currentSearchName) {
                loadNameSearchResults(currentSearchName, page);
            } else {
                // 瀏覽模式，使用一般分頁
                loadProfiles(page, currentNationality);
            }
        }

        // 執行搜尋
        async function performSearch() {
            const name = nameSearch.value.trim();
            const nationality = nationalityFilter.value.trim();

            searchResult.innerHTML = '';

            // 判斷是否有查詢條件
            const hasSearchConditions = name || nationality;

            if (hasSearchConditions) {
                // 查詢模式：顯示查詢結果在表格中
                if (name) {
                    // 有姓名查詢時，載入分頁查詢結果
                    loadNameSearchResults(name, 1);
                } else if (nationality) {
                    // 只有國籍過濾時，載入過濾後的分頁資料
                    loadProfiles(1, nationality);
                }
            } else {
                // 瀏覽模式：載入完整資料庫
                currentSearchName = '';
                loadProfiles(1, '');
            }
        }

        // 載入姓名查詢結果（分頁）
        async function loadNameSearchResults(name, page = 1) {
            if (isLoading) return;

            isLoading = true;
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">正在查詢...</td></tr>';

            try {
                const params = new URLSearchParams({
                    name: name,
                    page: page,
                    per_page: 20
                });

                const response = await fetch(`/query?${params}`, {
                    credentials: 'include'
                });

                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }

                if (response.status === 429) {
                    const data = await response.json();
                    showTableMessage(data.message || '已達到查詢限制', 'error');
                    updateQueryStats(data.query_stats);
                    return;
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                // 更新查詢統計
                if (data.query_stats) {
                    updateQueryStats(data.query_stats);
                }

                if (!data.found || data.total === 0) {
                    showTableMessage('沒有找到相符的姓名資料', 'info');
                    return;
                }

                // 設置當前查詢狀態
                currentSearchName = name;
                currentPage = data.page;
                totalPages = data.total_pages;
                currentNationality = '';

                // 渲染查詢結果
                renderSearchResultTable(data.profiles, page);
                renderSearchPagination(data);
                updateSearchPageInfo(data, name);

                // 確保分頁控制顯示
                pagination.style.display = 'flex';

            } catch (error) {
                showTableMessage(`查詢失敗: ${error.message}`, 'error');
            } finally {
                isLoading = false;
            }
        }

        // 清除過濾條件
        function clearFilters() {
            nameSearch.value = '';
            nationalityFilter.value = '';
            searchResult.innerHTML = '';
            currentSearchName = '';
            loadProfiles(1, '');
        }

        // 渲染查詢結果表格
        function renderSearchResultTable(profiles, page) {
            if (profiles.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: #666;">沒有找到符合條件的資料</td></tr>';
                return;
            }

            const startIndex = (page - 1) * 20;
            tableBody.innerHTML = profiles.map((profile, index) => `
                <tr>
                    <td>${startIndex + index + 1}</td>
                    <td><strong>${escapeHtml(profile.name)}</strong></td>
                    <td>${escapeHtml(profile.nationality)} ${profile.year ? `<span class="badge">${profile.year}</span>` : ''}</td>
                    <td>${escapeHtml(profile.passport_no)}</td>
                    <td>${profile.year || '-'}</td>
                </tr>
            `).join('');
        }

        // 渲染查詢結果分頁
        function renderSearchPagination(data) {
            if (data.total_pages <= 1) {
                pagination.innerHTML = '';
                return;
            }

            let html = '';

            // 上一頁
            html += `<button ${!data.has_prev ? 'disabled' : ''} onclick="changeSearchPage(${data.page - 1})">‹ 上一頁</button>`;

            // 頁碼
            const startPage = Math.max(1, data.page - 2);
            const endPage = Math.min(data.total_pages, data.page + 2);

            if (startPage > 1) {
                html += `<button onclick="changeSearchPage(1)">1</button>`;
                if (startPage > 2) html += `<span>...</span>`;
            }

            for (let i = startPage; i <= endPage; i++) {
                html += `<button ${i === data.page ? 'class="active"' : ''} onclick="changeSearchPage(${i})">${i}</button>`;
            }

            if (endPage < data.total_pages) {
                if (endPage < data.total_pages - 1) html += `<span>...</span>`;
                html += `<button onclick="changeSearchPage(${data.total_pages})">${data.total_pages}</button>`;
            }

            // 下一頁
            html += `<button ${!data.has_next ? 'disabled' : ''} onclick="changeSearchPage(${data.page + 1})">下一頁 ›</button>`;

            pagination.innerHTML = html;
        }

        // 更新查詢結果頁面資訊
        function updateSearchPageInfo(data, searchName) {
            pageInfo.textContent = `姓名查詢結果："${searchName}" • 第 ${data.page} 頁，共 ${data.total_pages} 頁 • 總計 ${data.total} 筆資料`;
        }

        // 切換查詢結果頁面
        function changeSearchPage(page) {
            if (page === currentPage || isLoading) return;
            if (currentSearchName) {
                loadNameSearchResults(currentSearchName, page);
            }
        }

        // 在表格中顯示訊息
        function showTableMessage(message, type = 'info') {
            const className = type === 'error' ? 'error' : 'info';
            pageInfo.textContent = message;
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: ${type === 'error' ? '#c53030' : '#666'};">
                        ${escapeHtml(message)}
                    </td>
                </tr>
            `;
            pagination.style.display = 'none';
        }

        // HTML 轉義
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // 更改密碼功能
        function showChangePasswordModal() {
            const modal = document.getElementById('changePasswordModal');
            modal.style.display = 'block';
        }

        function hideChangePasswordModal() {
            const modal = document.getElementById('changePasswordModal');
            modal.style.display = 'none';
            document.getElementById('changePasswordForm').reset();
        }

        async function changePassword() {
            const oldPassword = document.getElementById('oldPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (!oldPassword || !newPassword || !confirmPassword) {
                alert('請填寫所有欄位');
                return;
            }

            if (newPassword !== confirmPassword) {
                alert('新密碼和確認密碼不一致');
                return;
            }

            if (newPassword.length < 6) {
                alert('新密碼長度至少需要6個字符');
                return;
            }

            try {
                const response = await fetch('/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cookie': document.cookie
                    },
                    body: JSON.stringify({
                        old_password: oldPassword,
                        new_password: newPassword
                    })
                });

                const result = await response.json();

                if (result.success) {
                    alert('密碼更改成功！請重新登入');
                    logout();
                } else {
                    alert(result.message || '密碼更改失敗');
                }
            } catch (error) {
                console.error('更改密碼錯誤:', error);
                alert('更改密碼時發生錯誤');
            }

            hideChangePasswordModal();
        }
    </script>

    <!-- 更改密碼模態對話框 -->
    <div id="changePasswordModal"
        style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5);">
        <div
            style="background-color: white; margin: 10% auto; padding: 2rem; border-radius: 8px; width: 90%; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h3 style="margin: 0; color: #333;">更改密碼</h3>
                <button onclick="hideChangePasswordModal()"
                    style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">&times;</button>
            </div>

            <form id="changePasswordForm" onsubmit="event.preventDefault(); changePassword();">
                <div style="margin-bottom: 1rem;">
                    <label for="oldPassword"
                        style="display: block; margin-bottom: 0.5rem; font-weight: 500;">舊密碼</label>
                    <input type="password" id="oldPassword" required
                        style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem;">
                </div>

                <div style="margin-bottom: 1rem;">
                    <label for="newPassword"
                        style="display: block; margin-bottom: 0.5rem; font-weight: 500;">新密碼</label>
                    <input type="password" id="newPassword" required
                        style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem;">
                    <small style="color: #666; font-size: 0.875rem;">密碼長度至少需要6個字符</small>
                </div>

                <div style="margin-bottom: 1.5rem;">
                    <label for="confirmPassword"
                        style="display: block; margin-bottom: 0.5rem; font-weight: 500;">確認新密碼</label>
                    <input type="password" id="confirmPassword" required
                        style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem;">
                </div>

                <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                    <button type="button" onclick="hideChangePasswordModal()"
                        style="padding: 0.75rem 1.5rem; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">取消</button>
                    <button type="submit"
                        style="padding: 0.75rem 1.5rem; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">確認更改</button>
                </div>
            </form>
        </div>
    </div>

</body>

</html>
```

# Dockerfile
```
FROM python:3.11-slim

WORKDIR /app

# 安裝系統相依（pdfplumber 需要部分字型/依賴時可擴充）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

```

