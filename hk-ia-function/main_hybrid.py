#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合版本 AML 查詢系統
- 使用 SQLite 查詢 AML 資料
- 使用 Firebase Auth 進行會員驗證
"""

import os
import sqlite3
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask import Flask, request, jsonify, render_template, make_response
from datetime import datetime
import logging

# 設定 Firebase 模擬器環境
os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8081'
os.environ['FIREBASE_AUTH_EMULATOR_HOST'] = '127.0.0.1:9099'

# 初始化 Firebase
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(options={'projectId': 'hk-insurance-crawler'})

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False

# SQLite 資料庫路徑
DB_PATH = '/home/weschen/HK_insurance/aml_profiles.db'

def get_db_connection():
    """獲取 SQLite 資料庫連接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def verify_firebase_token(token):
    """驗證 Firebase token"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token 驗證失敗: {e}")
        return None

def get_user_info(uid):
    """從 Firestore 獲取用戶資訊"""
    try:
        db = firestore.client()
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"獲取用戶資訊失敗: {e}")
        return None

@app.route('/')
def index():
    """首頁 - 重定向到登入頁面"""
    return render_template('login_firebase.html')

@app.route('/login')
def login():
    """登入頁面"""
    return render_template('login_firebase.html')

@app.route('/register')
def register():
    """註冊頁面"""
    return render_template('register_firebase.html')

@app.route('/query')
def query_page():
    """查詢頁面 - 需要認證"""
    return render_template('query_hybrid.html')

@app.route('/api/stats')
def api_stats():
    """獲取統計資訊 - 需要認證"""
    # 檢查 token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': '需要登入'}), 401
    
    token = auth_header.split(' ')[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return jsonify({'error': '認證失敗'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取總數據統計
        cursor.execute("SELECT COUNT(*) as total FROM profiles")
        total = cursor.fetchone()['total']
        
        # 獲取年份統計
        cursor.execute("""
            SELECT SUBSTR(date, 1, 4) as year, COUNT(*) as count 
            FROM profiles 
            WHERE date IS NOT NULL 
            GROUP BY SUBSTR(date, 1, 4) 
            ORDER BY year DESC
        """)
        year_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'total': total,
            'yearStats': year_stats,
            'message': f'共有 {total} 筆 AML 資料'
        })
        
    except Exception as e:
        return jsonify({'error': f'統計查詢失敗: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜尋 AML 資料 - 需要認證"""
    # 檢查 token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': '需要登入'}), 401
    
    token = auth_header.split(' ')[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return jsonify({'error': '認證失敗'}), 401
    
    # 獲取用戶詳細資訊
    user_data = get_user_info(user_info['uid'])
    if not user_data:
        return jsonify({'error': '用戶資料不存在'}), 401
    
    # 檢查查詢權限
    query_limit = user_data.get('queryLimit', 5)
    queries_used = user_data.get('queriesUsed', 0)
    
    if query_limit != -1 and queries_used >= query_limit:
        return jsonify({'error': f'查詢次數已用完 ({queries_used}/{query_limit})'}), 403
    
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': '請輸入查詢關鍵字'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 搜尋查詢
        search_sql = """
            SELECT * FROM profiles 
            WHERE name_en LIKE ? OR name_zh LIKE ? OR name_other LIKE ? 
            ORDER BY date DESC LIMIT 100
        """
        search_term = f'%{keyword}%'
        cursor.execute(search_sql, (search_term, search_term, search_term))
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # 更新查詢次數（只有非管理員才扣除）
        if user_data.get('role') != 'admin' and query_limit != -1:
            try:
                db = firestore.client()
                db.collection('users').document(user_info['uid']).update({
                    'queriesUsed': queries_used + 1,
                    'lastLoginAt': firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"更新查詢次數失敗: {e}")
        
        return jsonify({
            'results': results,
            'total': len(results),
            'keyword': keyword,
            'userInfo': {
                'role': user_data.get('role'),
                'queryLimit': query_limit,
                'queriesUsed': queries_used + (1 if user_data.get('role') != 'admin' and query_limit != -1 else 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 啟動混合版 AML 查詢系統...")
    print(f"📊 SQLite 資料庫: {DB_PATH}")
    print(f"🔥 Firebase Auth: 127.0.0.1:9099")
    print(f"🔥 Firestore: 127.0.0.1:8081")
    print(f"🌐 網址: http://127.0.0.1:8000")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
