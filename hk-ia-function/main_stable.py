#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穩定版 AML 查詢系統
- 修復會話問題
- 簡化登入流程
- 預設管理員帳號: astcws@hotmail / admin123
"""

import os
import sqlite3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from datetime import datetime
import hashlib

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'hk-insurance-secret-key-2024-stable'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小時

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
    print(f"🔐 嘗試登入: {email}")
    if email in USERS:
        password_hash = hashlib.md5(password.encode()).hexdigest()
        stored_hash = USERS[email]['password']
        print(f"🔑 密碼比對: {password_hash} vs {stored_hash}")
        if stored_hash == password_hash:
            print("✅ 登入成功")
            return USERS[email]
        else:
            print("❌ 密碼錯誤")
    else:
        print("❌ 用戶不存在")
    return None

def is_logged_in():
    """檢查是否已登入"""
    logged_in = 'user_email' in session
    print(f"🔍 登入狀態檢查: {logged_in}")
    if logged_in:
        print(f"👤 當前用戶: {session.get('user_email')}")
    return logged_in

@app.route('/')
def index():
    """首頁"""
    print("🏠 訪問首頁")
    if is_logged_in():
        print("➡️ 重定向到查詢頁面")
        return redirect(url_for('query_page'))
    print("➡️ 顯示登入頁面")
    return render_template('login_simple.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"📨 登入請求: {email}")
        
        user = authenticate_user(email, password)
        if user:
            session.permanent = True
            session['user_email'] = email
            session['user_role'] = user['role']
            session['query_limit'] = user['queryLimit']
            session['queries_used'] = user['queriesUsed']
            print(f"✅ 設置會話: {dict(session)}")
            return redirect(url_for('query_page'))
        else:
            print("❌ 登入失敗，顯示錯誤")
            return render_template('login_simple.html', error='帳號或密碼錯誤')
    
    print("📄 顯示登入表單")
    return render_template('login_simple.html')

@app.route('/logout')
def logout():
    """登出"""
    print("👋 用戶登出")
    session.clear()
    return redirect(url_for('login'))

@app.route('/query')
def query_page():
    """查詢頁面 - 需要登入"""
    print("🔍 訪問查詢頁面")
    if not is_logged_in():
        print("❌ 未登入，重定向到登入頁面")
        return redirect(url_for('login'))
    print("✅ 已登入，顯示查詢頁面")
    return render_template('query_simple.html')

@app.route('/api/stats')
def api_stats():
    """獲取統計資訊"""
    if not is_logged_in():
        return jsonify({'error': '需要登入'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取總記錄數
        cursor.execute("SELECT COUNT(*) as total FROM profiles")
        total_count = cursor.fetchone()['total']
        
        # 獲取最新記錄
        cursor.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1")
        latest_record = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'total_records': total_count,
            'latest_record': dict(latest_record) if latest_record else None,
            'user_email': session.get('user_email'),
            'user_role': session.get('user_role')
        })
    except Exception as e:
        return jsonify({'error': f'獲取統計失敗: {str(e)}'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """搜尋 API"""
    if not is_logged_in():
        return jsonify({'error': '需要登入'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求資料'}), 400
        
        search_type = data.get('type', '')
        search_value = data.get('value', '').strip()
        
        if not search_value:
            return jsonify({'error': '請輸入搜尋內容'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 根據搜尋類型構建查詢
        if search_type == 'name':
            query = "SELECT * FROM profiles WHERE chinese_name LIKE ? OR english_name LIKE ? ORDER BY id DESC LIMIT 100"
            params = (f'%{search_value}%', f'%{search_value}%')
        elif search_type == 'document':
            query = "SELECT * FROM profiles WHERE passport_number LIKE ? OR id_card_number LIKE ? ORDER BY id DESC LIMIT 100"
            params = (f'%{search_value}%', f'%{search_value}%')
        elif search_type == 'date':
            query = "SELECT * FROM profiles WHERE birth_date LIKE ? ORDER BY id DESC LIMIT 100"
            params = (f'%{search_value}%',)
        else:
            # 全文搜尋
            query = """SELECT * FROM profiles WHERE 
                      chinese_name LIKE ? OR english_name LIKE ? OR 
                      passport_number LIKE ? OR id_card_number LIKE ? OR
                      birth_date LIKE ? OR nationality LIKE ? OR
                      address LIKE ? OR alias LIKE ?
                      ORDER BY id DESC LIMIT 100"""
            params = tuple([f'%{search_value}%'] * 8)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 轉換為字典列表
        results_list = [dict(row) for row in results]
        
        conn.close()
        
        return jsonify({
            'results': results_list,
            'count': len(results_list),
            'search_type': search_type,
            'search_value': search_value
        })
        
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 啟動穩定版 AML 查詢系統...")
    print(f"📊 SQLite 資料庫: {DB_PATH}")
    print(f"👤 預設管理員: astcws@hotmail / admin123")
    print(f"🌐 網址: http://127.0.0.1:5000")
    print("📝 除錯訊息已啟用")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
