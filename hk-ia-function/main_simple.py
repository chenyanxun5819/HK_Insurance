"""
簡化版 Firebase Authentication 集成
基於現有 AML 查詢系統，添加 Firebase Auth 支持
"""
from flask import Flask, request, jsonify, render_template, make_response
from firestore_aml_query import FirestoreAMLQuery
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

# 🚀 初始化 Firestore AML 查詢引擎
USE_EMULATOR = os.environ.get('FIRESTORE_EMULATOR_HOST') is not None
print(f"🚀 初始化 Firestore AML 查詢引擎 ({'模擬器模式' if USE_EMULATOR else 'GCP生產模式'})...")
aml_query = FirestoreAMLQuery(use_emulator=USE_EMULATOR)

@app.route("/")
def home():
    """主頁 - 使用 Firebase Auth 版本的模板"""
    response = make_response(render_template("query_firebase.html"))
    
    # 🔥 添加強制無快取標頭
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    
    return response

@app.route("/login")
def login_page():
    """登入頁面"""
    response = make_response(render_template("login_firebase.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/register")
def register_page():
    """註冊頁面"""
    response = make_response(render_template("register_firebase.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

@app.route("/admin")
def admin_page():
    """管理員頁面 - 簡化版"""
    response = make_response("<h1>管理員面板</h1><p>Firebase Auth 管理功能開發中...</p><a href='/'>返回首頁</a>")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    return response

# ==================== API 端點 ====================

def verify_auth_header():
    """簡化的認證檢查 - 只檢查 Bearer token 存在"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    return True

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """檢查身份驗證狀態 - 簡化版"""
    if not verify_auth_header():
        return jsonify({'error': '未提供有效的身份驗證令牌'}), 401
        
    return jsonify({
        'authenticated': True,
        'user': {
            'uid': 'demo-user',
            'email': 'demo@example.com',
            'role': 'user',
            'email_verified': True
        }
    })

@app.route("/query_name", methods=["POST"])
def query_name_api():
    """AML 查詢 API - 需要身份驗證"""
    if not verify_auth_header():
        return jsonify({'error': '請先登入'}), 401
        
    try:
        data = request.get_json()
        name_input = data.get('name', '').strip()
        
        if not name_input:
            return jsonify({'error': '請輸入查詢名稱'}), 400
        
        # 記錄查詢活動
        logger.info(f"用戶查詢: {name_input}")
        
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
def get_profiles():
    """獲取 AML 資料 - 需要身份驗證"""
    if not verify_auth_header():
        return jsonify({'error': '請先登入'}), 401
        
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
    print(f"🚀 啟動簡化版 Firebase Auth AML 查詢系統於 http://127.0.0.1:{port}")
    print(f"📋 使用說明:")
    print(f"   🔐 登入頁面: http://127.0.0.1:{port}/login")
    print(f"   📝 註冊頁面: http://127.0.0.1:{port}/register") 
    print(f"   🏠 主頁查詢: http://127.0.0.1:{port}/")
    print(f"   🔥 Firebase Auth Emulator: http://127.0.0.1:9099")
    print(f"   📊 Firestore Emulator: http://127.0.0.1:8081")
    app.run(host="0.0.0.0", port=port, debug=True)
