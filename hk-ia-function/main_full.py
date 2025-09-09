#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整會員制度 AML 查詢系統
根據 member.md 規格實現完整功能
"""

import os
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from datetime import datetime, timedelta
import re

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'hk-insurance-member-system-2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 資料庫路徑
MEMBERS_DB = '/home/weschen/HK_insurance/members.db'
AML_DB = '/home/weschen/HK_insurance/aml_profiles.db'

# SendGrid API Key (從 member.md)
SENDGRID_API_KEY = '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'

def get_members_db():
    """獲取會員資料庫連接"""
    conn = sqlite3.connect(MEMBERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_aml_db():
    """獲取 AML 資料庫連接"""
    conn = sqlite3.connect(AML_DB)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_value):
    """驗證密碼"""
    return hash_password(password) == hash_value

def is_valid_email(email):
    """驗證 Email 格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(to_email, subject, body):
    """發送郵件 (模擬)"""
    # 在實際部署中使用 SendGrid API
    print(f"📧 發送郵件到: {to_email}")
    print(f"📧 主題: {subject}")
    print(f"📧 內容: {body}")
    return True

def generate_token():
    """生成安全令牌"""
    return secrets.token_urlsafe(32)

def get_current_user():
    """獲取當前用戶資訊"""
    if 'user_id' not in session:
        return None
    
    conn = get_members_db()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ? AND status = "active"',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    return user

def require_login(f):
    """登入裝飾器"""
    def wrapper(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def require_role(role):
    """角色權限裝飾器"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or user['role'] != role:
                flash('權限不足', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@app.context_processor
def inject_user():
    """全域注入當前用戶資訊"""
    user = get_current_user()
    return dict(current_user=user, user=user)

@app.route('/')
def index():
    """首頁 - 整合查詢功能"""
    user = get_current_user()
    return render_template('index.html', user=user, current_user=user)

@app.route('/search', methods=['POST'])
def search():
    """AML 查詢 API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '無效的請求資料'}), 400
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'message': '請輸入姓名'}), 400

        # 檢查是否為登入用戶
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'message': '請先登入'}), 401
        
        # 檢查郵件是否已驗證
        if not user['email_verified']:
            return jsonify({'success': False, 'message': '請先驗證您的郵件地址才能進行查詢'}), 403
        
        # 檢查查詢次數限制（基本會員總共5次，不是每日）
        if user['query_limit'] != -1 and user['queries_used'] >= user['query_limit']:
            return jsonify({'success': False, 'message': '查詢次數已用完（基本會員總共可查詢5次）'}), 403

        # 執行查詢
        conn = get_aml_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT name, nationality, passport_no, year, source_url as source 
        FROM profiles 
        WHERE name LIKE ? 
        ORDER BY name
        ''', (f'%{name}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        # 增加查詢次數
        if user['query_limit'] != -1:
            members_conn = get_members_db()
            members_cursor = members_conn.cursor()
            members_cursor.execute('''
            UPDATE users SET queries_used = queries_used + 1, updated_at = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), user['id']))
            members_conn.commit()
            members_conn.close()
        
        # 轉換結果格式
        matches = []
        for row in results:
            matches.append({
                'name': row['name'] or '',
                'nationality': row['nationality'] or '',
                'passport_no': row['passport_no'] or '',
                'year': str(row['year']) if row['year'] else '',
                'source': row['source'] or ''
            })
        
        return jsonify({
            'success': True,
            'found': len(matches) > 0,
            'matches': matches,
            'total': len(matches),
            'remaining_queries': user['query_limit'] - user['queries_used'] - 1 if user['query_limit'] != -1 else -1
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'查詢錯誤: {str(e)}'}), 500

@app.route('/statistics')
def statistics():
    """統計資訊 API"""
    try:
        conn = get_aml_db()
        cursor = conn.cursor()
        
        # 總計
        cursor.execute('SELECT COUNT(*) as total FROM aml_profiles')
        total = cursor.fetchone()['total']
        
        # 年份統計
        cursor.execute('''
        SELECT year, COUNT(*) as count 
        FROM aml_profiles 
        GROUP BY year 
        ORDER BY year
        ''')
        year_stats = {}
        for row in cursor.fetchall():
            year = str(row['year']) if row['year'] else '未知'
            year_stats[year] = row['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': total,
            'year_stats': year_stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'統計錯誤: {str(e)}'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """會員註冊"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 驗證輸入
        if not email or not password:
            flash('請填寫所有必填欄位', 'error')
            return render_template('register.html')
        
        if not is_valid_email(email):
            flash('請輸入有效的 Email 地址', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密碼至少需要 6 個字符', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('密碼確認不一致', 'error')
            return render_template('register.html')
        
        conn = get_members_db()
        
        # 檢查 Email 是否已存在
        existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('此 Email 已被註冊', 'error')
            conn.close()
            return render_template('register.html')
        
        # 創建新用戶
        password_hash = hash_password(password)
        current_time = datetime.now().isoformat()
        
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (email, password_hash, role, status, query_limit, queries_used, 
                          email_verified, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, 'basic', 'active', 5, 0, 0, current_time, current_time))
        
        user_id = cursor.lastrowid
        
        # 生成驗證令牌
        token = generate_token()
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        cursor.execute('''
        INSERT INTO email_verifications (email, token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        ''', (email, token, current_time, expires_at))
        
        conn.commit()
        conn.close()
        
        # 發送驗證郵件
        verification_link = f"http://127.0.0.1:5000/verify-email?token={token}"
        send_email(
            email,
            "AML 查詢系統 - Email 驗證",
            f"請點擊以下連結驗證您的 Email：\n{verification_link}"
        )
        
        flash('註冊成功！請檢查您的 Email 並點擊驗證連結，驗證後即可獲得5次查詢機會', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/verify-email')
def verify_email():
    """Email 驗證"""
    token = request.args.get('token')
    if not token:
        flash('無效的驗證連結', 'error')
        return redirect(url_for('login'))
    
    conn = get_members_db()
    verification = conn.execute('''
    SELECT * FROM email_verifications 
    WHERE token = ? AND used = 0 AND expires_at > ?
    ''', (token, datetime.now().isoformat())).fetchone()
    
    if not verification:
        flash('驗證連結已過期或無效', 'error')
        conn.close()
        return redirect(url_for('login'))
    
    # 更新用戶驗證狀態
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET email_verified = 1 WHERE email = ?', (verification['email'],))
    cursor.execute('UPDATE email_verifications SET used = 1 WHERE id = ?', (verification['id'],))
    
    conn.commit()
    conn.close()
    
    flash('Email 驗證成功！您現在可以登入並使用5次查詢機會', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """會員登入"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('請輸入 Email 和密碼', 'error')
            return render_template('login.html')
        
        conn = get_members_db()
        user = conn.execute('''
        SELECT * FROM users WHERE email = ? AND status = "active"
        ''', (email,)).fetchone()
        
        if not user:
            flash('Email 或密碼錯誤', 'error')
            conn.close()
            return render_template('login.html')
        
        # 檢查帳號鎖定
        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                flash('帳號暫時鎖定，請稍後再試', 'error')
                conn.close()
                return render_template('login.html')
        
        if verify_password(password, user['password_hash']):
            # 登入成功
            session.permanent = True
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            # 重置失敗次數，更新最後登入時間
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE users SET failed_login_attempts = 0, locked_until = NULL,
                           last_login_at = ?, last_login_ip = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), request.remote_addr, user['id']))
            
            conn.commit()
            conn.close()
            
            # 登入成功後重定向到首頁
            return redirect(url_for('index'))
        else:
            # 登入失敗
            cursor = conn.cursor()
            failed_attempts = user['failed_login_attempts'] + 1
            
            if failed_attempts >= 5:
                # 鎖定帳號 30 分鐘
                locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                cursor.execute('''
                UPDATE users SET failed_login_attempts = ?, locked_until = ?
                WHERE id = ?
                ''', (failed_attempts, locked_until, user['id']))
                flash('登入失敗次數過多，帳號已鎖定 30 分鐘', 'error')
            else:
                cursor.execute('''
                UPDATE users SET failed_login_attempts = ?
                WHERE id = ?
                ''', (failed_attempts, user['id']))
                flash(f'Email 或密碼錯誤 (剩餘嘗試次數: {5-failed_attempts})', 'error')
            
            conn.commit()
            conn.close()
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('已成功登出', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@require_role('admin')
def admin_dashboard():
    """管理員後台"""
    conn = get_members_db()
    cursor = conn.cursor()
    
    # 獲取統計資料
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'paid'")
    paid_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(created_at) = DATE('now')")
    today_queries = cursor.fetchone()[0]
    
    # 獲取 AML 記錄總數
    aml_conn = get_aml_db()
    aml_cursor = aml_conn.cursor()
    aml_cursor.execute("SELECT COUNT(*) FROM profiles")
    total_records = aml_cursor.fetchone()[0]
    aml_conn.close()
    
    # 獲取最新用戶
    cursor.execute("""
        SELECT id, email, role, email_verified, created_at 
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    recent_users = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    
    stats = {
        'total_users': total_users,
        'paid_users': paid_users,
        'today_queries': today_queries,
        'total_records': total_records
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)

@app.route('/member/dashboard')
@require_login
def member_dashboard():
    """會員後台"""
    user = get_current_user()
    
    conn = get_members_db()
    cursor = conn.cursor()
    
    # 獲取查詢記錄
    cursor.execute("""
        SELECT keyword, result_count, created_at 
        FROM query_logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user['id'],))
    query_logs = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    conn.close()
    return render_template('member/dashboard.html', user=user, query_logs=query_logs)

@app.route('/dashboard')
@require_login
def dashboard():
    """重定向到會員後台"""
    return redirect(url_for('member_dashboard'))

@app.route('/search')
@require_login
def search_page():
    """AML 查詢頁面"""
    user = get_current_user()
    
    # 獲取可用年份
    aml_conn = get_aml_db()
    aml_cursor = aml_conn.cursor()
    aml_cursor.execute("SELECT DISTINCT year FROM profiles ORDER BY year DESC")
    available_years = [row[0] for row in aml_cursor.fetchall()]
    aml_conn.close()
    
    return render_template('member/search.html', user=user, available_years=available_years)

@app.route('/admin/users')
@require_role('admin')
def admin_users():
    """用戶管理頁面"""
    conn = get_members_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, role, query_limit, queries_used, email_verified, 
               created_at, last_login_at 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/api/search', methods=['POST'])
@require_login
def api_search():
    """AML 搜尋 API"""
    user = get_current_user()
    
    # 檢查郵件是否已驗證
    if not user['email_verified']:
        return jsonify({'error': '請先驗證您的郵件地址才能進行查詢'}), 403
    
    # 檢查查詢次數限制（基本會員總共5次，不是每日）
    if user['query_limit'] != -1 and user['queries_used'] >= user['query_limit']:
        return jsonify({'error': '查詢次數已用完（基本會員總共可查詢5次）'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '無效的請求資料'}), 400
        
        search_type = data.get('type', '')
        search_value = data.get('value', '').strip()
        
        if not search_value:
            return jsonify({'error': '請輸入搜尋內容'}), 400
        
        conn = get_aml_db()
        cursor = conn.cursor()
        
        # 根據搜尋類型構建查詢
        if search_type == 'name':
            query = "SELECT * FROM profiles WHERE name LIKE ? ORDER BY id DESC LIMIT 50"
            params = (f'%{search_value}%',)
        elif search_type == 'nationality':
            query = "SELECT * FROM profiles WHERE nationality LIKE ? ORDER BY id DESC LIMIT 50"
            params = (f'%{search_value}%',)
        elif search_type == 'passport':
            query = "SELECT * FROM profiles WHERE passport_no LIKE ? ORDER BY id DESC LIMIT 50"
            params = (f'%{search_value}%',)
        else:
            # 全文搜尋
            query = """SELECT * FROM profiles WHERE 
                      name LIKE ? OR nationality LIKE ? OR 
                      passport_no LIKE ?
                      ORDER BY id DESC LIMIT 50"""
            params = (f'%{search_value}%', f'%{search_value}%', f'%{search_value}%')
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 轉換為字典列表
        results_list = [dict(row) for row in results]
        
        conn.close()
        
        # 更新查詢次數和記錄
        if user['query_limit'] != -1:
            members_conn = get_members_db()
            members_cursor = members_conn.cursor()
            
            # 更新查詢次數
            members_cursor.execute('''
            UPDATE users SET queries_used = queries_used + 1, updated_at = ?
            WHERE id = ?
            ''', (datetime.now().isoformat(), user['id']))
            
            # 記錄查詢日誌
            members_cursor.execute('''
            INSERT INTO query_logs (user_id, keyword, result_count, created_at)
            VALUES (?, ?, ?, ?)
            ''', (user['id'], search_value, len(results_list), datetime.now().isoformat()))
            
            members_conn.commit()
            members_conn.close()
        
        return jsonify({
            'results': results_list,
            'count': len(results_list),
            'search_type': search_type,
            'search_value': search_value,
            'remaining_queries': user['query_limit'] - user['queries_used'] - 1 if user['query_limit'] != -1 else -1
        })
        
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@require_role('admin')
def admin_edit_user(user_id):
    """管理員 - 編輯用戶"""
    try:
        data = request.get_json()
        role = data.get('role')
        query_limit = data.get('query_limit', 5)
        status = data.get('status', 'active')
        
        if role not in ['admin', 'paid', 'basic']:
            return jsonify({'error': '無效的角色'}), 400
        
        if status not in ['active', 'suspended', 'deleted']:
            return jsonify({'error': '無效的狀態'}), 400
        
        conn = get_members_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE users SET role = ?, query_limit = ?, status = ?, updated_at = ?
        WHERE id = ?
        ''', (role, query_limit, status, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '用戶資料已更新'})
        
    except Exception as e:
        return jsonify({'error': f'更新失敗: {str(e)}'}), 500

@app.route('/admin/reset-queries', methods=['POST'])
@require_role('admin')
def admin_reset_queries():
    """管理員 - 重置所有用戶查詢次數"""
    try:
        conn = get_members_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET queries_used = 0, updated_at = ?', 
                      (datetime.now().isoformat(),))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'已重置 {affected_rows} 位用戶的查詢次數'
        })
        
    except Exception as e:
        return jsonify({'error': f'重置失敗: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/logs')
@require_role('admin')
def admin_user_logs(user_id):
    """查看用戶查詢記錄"""
    conn = get_members_db()
    
    # 獲取用戶資訊
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('用戶不存在', 'error')
        return redirect(url_for('admin_users'))
    
    # 獲取查詢記錄
    logs = conn.execute('''
    SELECT keyword, result_count, created_at FROM query_logs 
    WHERE user_id = ? ORDER BY created_at DESC LIMIT 100
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin/user_logs.html', user=user, logs=logs)

@app.route('/change-password', methods=['GET', 'POST'])
@require_login
def change_password():
    """修改密碼"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('請填寫所有欄位', 'error')
            return render_template('account/change_password.html')
        
        if len(new_password) < 6:
            flash('新密碼至少需要 6 個字符', 'error')
            return render_template('account/change_password.html')
        
        if new_password != confirm_password:
            flash('新密碼確認不一致', 'error')
            return render_template('account/change_password.html')
        
        user = get_current_user()
        
        # 驗證當前密碼
        if not verify_password(current_password, user['password_hash']):
            flash('當前密碼錯誤', 'error')
            return render_template('account/change_password.html')
        
        # 更新密碼
        new_password_hash = hash_password(new_password)
        
        conn = get_members_db()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE users SET password_hash = ?, updated_at = ?
        WHERE id = ?
        ''', (new_password_hash, datetime.now().isoformat(), user['id']))
        
        conn.commit()
        conn.close()
        
        flash('密碼已成功更新', 'success')
        return redirect(url_for('member_dashboard'))
    
    return render_template('account/change_password.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """忘記密碼"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('請輸入 Email 地址', 'error')
            return render_template('account/forgot_password.html')
        
        conn = get_members_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            # 生成重設令牌
            token = generate_token()
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
            
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO password_resets (email, token, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            ''', (email, token, datetime.now().isoformat(), expires_at))
            
            conn.commit()
            
            # 發送重設郵件
            reset_link = f"http://127.0.0.1:5000/account/reset-password?token={token}"
            send_email(
                email,
                "AML 查詢系統 - 密碼重設",
                f"請點擊以下連結重設您的密碼（有效期 1 小時）：\n{reset_link}"
            )
        
        conn.close()
        
        # 不論用戶是否存在都顯示相同訊息（安全考量）
        flash('如果該 Email 存在，我們已發送密碼重設連結到您的信箱', 'info')
        return redirect(url_for('login'))
    
    return render_template('account/forgot_password.html')

@app.route('/account/reset-password')
def reset_password():
    """重設密碼"""
    token = request.args.get('token')
    if not token:
        flash('無效的重設連結', 'error')
        return redirect(url_for('login'))
    
    conn = get_members_db()
    reset_record = conn.execute('''
    SELECT * FROM password_resets 
    WHERE token = ? AND used = 0 AND expires_at > ?
    ''', (token, datetime.now().isoformat())).fetchone()
    
    conn.close()
    
    if not reset_record:
        flash('重設連結已過期或無效', 'error')
        return redirect(url_for('login'))
    
    # 生成新密碼
    import string
    new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    new_password_hash = hash_password(new_password)
    
    conn = get_members_db()
    cursor = conn.cursor()
    
    # 更新密碼
    cursor.execute('''
    UPDATE users SET password_hash = ?, updated_at = ?
    WHERE email = ?
    ''', (new_password_hash, datetime.now().isoformat(), reset_record['email']))
    
    # 標記重設令牌為已使用
    cursor.execute('''
    UPDATE password_resets SET used = 1 WHERE id = ?
    ''', (reset_record['id'],))
    
    conn.commit()
    conn.close()
    
    # 發送新密碼
    send_email(
        reset_record['email'],
        "AML 查詢系統 - 新密碼",
        f"您的新密碼是：{new_password}\n\n請登入後立即修改密碼。"
    )
    
    flash('新密碼已發送到您的信箱', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("🚀 啟動完整會員制度 AML 查詢系統...")
    print(f"📊 會員資料庫: {MEMBERS_DB}")
    print(f"📊 AML 資料庫: {AML_DB}")
    print(f"👤 管理員帳號: astcws@hotmail / admin123")
    print(f"🌐 網址: http://127.0.0.1:5000")
    
    # 強制指定 host 和 port，確保可以連接
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
