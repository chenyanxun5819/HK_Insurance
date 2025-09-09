#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試版 AML 查詢系統 - 修復會話問題
"""

import os
import sqlite3
from flask import Flask, request, jsonify, session, redirect, url_for
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'hk-insurance-test-key-2024'

# SQLite 資料庫路徑
DB_PATH = '/home/weschen/HK_insurance/aml_profiles.db'

# 預設用戶
USERS = {
    'astcws@hotmail': {
        'password': hashlib.md5('admin123'.encode()).hexdigest(),
        'role': 'admin'
    }
}

def authenticate_user(email, password):
    """驗證用戶"""
    if email in USERS:
        password_hash = hashlib.md5(password.encode()).hexdigest()
        if USERS[email]['password'] == password_hash:
            return USERS[email]
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    """首頁"""
    if 'user_email' in session:
        return f"""
        <h1>歡迎！{session['user_email']}</h1>
        <p>登入狀態: 已登入</p>
        <p>角色: {session.get('user_role', 'unknown')}</p>
        <a href="/query">查詢頁面</a> | <a href="/logout">登出</a>
        """
    
    return '''
    <h1>AML 查詢系統登入</h1>
    <form method="POST" action="/login">
        <p>
            <label>Email:</label><br>
            <input type="email" name="email" value="astcws@hotmail" required>
        </p>
        <p>
            <label>密碼:</label><br>
            <input type="password" name="password" value="admin123" required>
        </p>
        <p>
            <button type="submit">登入</button>
        </p>
    </form>
    '''

@app.route('/login', methods=['POST'])
def login():
    """登入處理"""
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    print(f"🔐 登入嘗試: {email}")
    
    user = authenticate_user(email, password)
    if user:
        session['user_email'] = email
        session['user_role'] = user['role']
        print(f"✅ 登入成功，會話設置: {dict(session)}")
        return redirect(url_for('index'))
    else:
        print("❌ 登入失敗")
        return '''
        <h1>登入失敗</h1>
        <p>帳號或密碼錯誤</p>
        <a href="/">返回登入</a>
        '''

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/query')
def query_page():
    """查詢頁面"""
    if 'user_email' not in session:
        return redirect(url_for('index'))
    
    return f'''
    <h1>AML 查詢頁面</h1>
    <p>歡迎 {session['user_email']}</p>
    <p>角色: {session.get('user_role')}</p>
    <form method="POST" action="/search">
        <p>
            <label>搜尋姓名:</label><br>
            <input type="text" name="name" placeholder="輸入姓名">
        </p>
        <p>
            <button type="submit">搜尋</button>
        </p>
    </form>
    <a href="/">回首頁</a> | <a href="/logout">登出</a>
    '''

@app.route('/search', methods=['POST'])
def search():
    """搜尋功能"""
    if 'user_email' not in session:
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('query_page'))
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM profiles WHERE name LIKE ? LIMIT 10"
        cursor.execute(query, (f'%{name}%',))
        results = cursor.fetchall()
        
        html = f'''
        <h1>搜尋結果</h1>
        <p>搜尋關鍵字: {name}</p>
        <p>找到 {len(results)} 筆記錄</p>
        '''
        
        if results:
            html += '<table border="1"><tr><th>ID</th><th>姓名</th><th>國籍</th><th>護照號碼</th></tr>'
            for row in results:
                html += f'<tr><td>{row["id"]}</td><td>{row["name"]}</td><td>{row["nationality"]}</td><td>{row["passport_no"]}</td></tr>'
            html += '</table>'
        else:
            html += '<p>沒有找到符合的記錄</p>'
        
        html += '<br><a href="/query">重新搜尋</a> | <a href="/">回首頁</a>'
        
        conn.close()
        return html
        
    except Exception as e:
        return f'<h1>搜尋錯誤</h1><p>{str(e)}</p><a href="/query">重新搜尋</a>'

if __name__ == '__main__':
    print("🚀 啟動測試版 AML 查詢系統...")
    print(f"📊 SQLite 資料庫: {DB_PATH}")
    print(f"👤 測試帳號: astcws@hotmail / admin123")
    print(f"🌐 網址: http://127.0.0.1:3000")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
