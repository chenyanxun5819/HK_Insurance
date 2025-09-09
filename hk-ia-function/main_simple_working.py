#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版 AML 查詢系統
- 使用 SQLite 查詢 AML 資料  
- 使用簡單的 session 認證
- 預設管理員帳號: astcws@hotmail / admin123
"""

import os
import sqlite3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from datetime import datetime
import hashlib

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'hk-insurance-secret-key-2024'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# SQLite 資料庫路徑
DB_PATH = '/home/weschen/HK_insurance/aml_profiles.db'

# 預設用戶 (根據 member.md)
USERS = {
    'astcws@hotmail': {
        'password': hashlib.md5('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'queryLimit': -1,  # 無限制
        'queriesUsed': 0
    }
}

def get_db_connection():
    """獲取 SQLite 資料庫連接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def authenticate_user(email, password):
    """驗證用戶"""
    if email in USERS:
        password_hash = hashlib.md5(password.encode()).hexdigest()
        if USERS[email]['password'] == password_hash:
            return USERS[email]
    return None

def is_logged_in():
    """檢查是否已登入"""
    return 'user_email' in session

@app.route('/')
def index():
    """首頁"""
    if is_logged_in():
        return redirect(url_for('query_page'))
    return render_template('login_simple.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = authenticate_user(email, password)
        if user:
            session['user_email'] = email
            session['user_role'] = user['role']
            session['query_limit'] = user['queryLimit']
            session['queries_used'] = user['queriesUsed']
            return redirect(url_for('query_page'))
        else:
            return render_template('login_simple.html', error='帳號或密碼錯誤')
    
    return render_template('login_simple.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/query')
def query_page():
    """查詢頁面 - 需要登入"""
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('query_simple.html')

@app.route('/api/stats')
def api_stats():
    """獲取統計資訊"""
    if not is_logged_in():
        return jsonify({'error': '需要登入'}), 401
    
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
            'message': f'共有 {total} 筆 AML 反洗錢資料',
            'userInfo': {
                'email': session['user_email'],
                'role': session['user_role'],
                'queryLimit': session['query_limit'],
                'queriesUsed': session['queries_used']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'統計查詢失敗: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜尋 AML 資料"""
    if not is_logged_in():
        return jsonify({'error': '需要登入'}), 401
    
    # 檢查查詢權限
    query_limit = session.get('query_limit', 5)
    queries_used = session.get('queries_used', 0)
    
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
        
        # 更新查詢次數 (非管理員)
        if session.get('user_role') != 'admin' and query_limit != -1:
            session['queries_used'] = queries_used + 1
        
        return jsonify({
            'results': results,
            'total': len(results),
            'keyword': keyword,
            'userInfo': {
                'email': session['user_email'],
                'role': session['user_role'],
                'queryLimit': query_limit,
                'queriesUsed': session.get('queries_used', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 啟動簡化版 AML 查詢系統...")
    print(f"📊 SQLite 資料庫: {DB_PATH}")
    print(f"👤 預設管理員: astcws@hotmail / admin123")
    print(f"🌐 網址: http://127.0.0.1:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
