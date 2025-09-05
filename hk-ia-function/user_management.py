import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

class UserManager:
    def __init__(self, db_path='aml_profiles.db'):
        self.db_path = db_path
        self.init_tables()

    def init_tables(self):
        """初始化用戶管理相關的資料表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用戶表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            membership_level TEXT DEFAULT 'basic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0
        )
        ''')
        
        # 查詢記錄表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query_type TEXT,
            query_params TEXT,
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 用戶會話表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 密碼重置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            reset_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def hash_password(self, password):
        """密碼哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_session_token(self):
        """生成會話token"""
        return secrets.token_urlsafe(32)

    def register_user(self, email, password, membership_level='basic', is_admin=False):
        """註冊新用戶"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查email是否已存在
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return {'success': False, 'message': '此 Email 已被註冊'}
            
            # 創建新用戶
            password_hash = self.hash_password(password)
            cursor.execute('''
            INSERT INTO users (email, password_hash, membership_level, is_admin)
            VALUES (?, ?, ?, ?)
            ''', (email, password_hash, membership_level, is_admin))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '註冊成功', 'user_id': user_id}
            
        except Exception as e:
            return {'success': False, 'message': f'註冊失敗: {str(e)}'}

    def login_user(self, email, password):
        """用戶登入"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
            SELECT id, email, membership_level, is_admin FROM users 
            WHERE email = ? AND password_hash = ? AND is_active = 1
            ''', (email, password_hash))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {'success': False, 'message': '帳號或密碼錯誤'}
            
            user_id, email, membership_level, is_admin = user
            
            # 創建會話
            session_token = self.generate_session_token()
            expires_at = datetime.now() + timedelta(hours=24)  # 24小時有效
            
            cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            # 更新最後登入時間
            cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'session_token': session_token,
                'user': {
                    'id': user_id,
                    'email': email,
                    'membership_level': membership_level,
                    'is_admin': is_admin
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'登入失敗: {str(e)}'}

    def verify_session(self, session_token):
        """驗證會話"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT u.id, u.email, u.membership_level, u.is_admin, s.expires_at
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND u.is_active = 1
            ''', (session_token,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'valid': False, 'message': '無效的會話'}
            
            user_id, email, membership_level, is_admin, expires_at = result
            
            # 檢查是否過期
            expires_at_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00')) if isinstance(expires_at, str) else expires_at
            if datetime.now() > expires_at_dt:
                # 刪除過期的會話
                cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
                conn.commit()
                conn.close()
                return {'valid': False, 'message': '會話已過期'}
            
            conn.close()
            
            return {
                'valid': True,
                'user': {
                    'id': user_id,
                    'email': email,
                    'membership_level': membership_level,
                    'is_admin': is_admin
                }
            }
            
        except Exception as e:
            print(f"會話驗證錯誤: {e}")
            return {'valid': False, 'message': '驗證失敗'}

    def logout_user(self, session_token):
        """用戶登出"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '登出成功'}
            
        except Exception as e:
            return {'success': False, 'message': f'登出失敗: {str(e)}'}

    def change_password(self, user_id, old_password, new_password):
        """更改密碼"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 驗證舊密碼
            old_password_hash = self.hash_password(old_password)
            cursor.execute('SELECT id FROM users WHERE id = ? AND password_hash = ?', (user_id, old_password_hash))
            
            if not cursor.fetchone():
                conn.close()
                return {'success': False, 'message': '舊密碼錯誤'}
            
            # 密碼強度檢查
            if len(new_password) < 6:
                conn.close()
                return {'success': False, 'message': '新密碼長度至少需要6個字符'}
            
            # 更新密碼
            new_password_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, user_id))
            
            # 清除該用戶的所有會話（強制重新登入）
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '密碼更改成功，請重新登入'}
            
        except Exception as e:
            return {'success': False, 'message': f'密碼更改失敗: {str(e)}'}

    def check_query_limit(self, user_id):
        """檢查用戶查詢限制"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 獲取用戶會員等級
            cursor.execute('SELECT membership_level FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return {'allowed': False, 'message': '用戶不存在'}
            
            membership_level = user[0]
            
            # 設定查詢限制
            if membership_level == 'basic':
                daily_limit = 5
            elif membership_level == 'premium':
                daily_limit = 100  # 付費會員
            elif membership_level == 'super':
                # 超級會員無限制
                conn.close()
                return {
                    'allowed': True,
                    'used': 0,
                    'limit': -1,  # -1 表示無限制
                    'remaining': -1
                }
            else:
                daily_limit = 5  # 預設為基本會員
            
            # 檢查今日查詢次數
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM query_logs 
                WHERE user_id = ? AND DATE(query_time) = ?
            ''', (user_id, today))
            
            today_queries = cursor.fetchone()[0]
            conn.close()
            
            if today_queries >= daily_limit:
                return {
                    'allowed': False, 
                    'message': f'已達今日查詢限制 ({today_queries}/{daily_limit})',
                    'used': today_queries,
                    'limit': daily_limit
                }
            
            return {
                'allowed': True,
                'used': today_queries,
                'limit': daily_limit,
                'remaining': daily_limit - today_queries
            }
            
        except Exception as e:
            print(f"檢查查詢限制錯誤: {e}")
            return {'allowed': False, 'message': '系統錯誤'}

    def log_query(self, user_id, query_type, query_params=None):
        """記錄查詢"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO query_logs (user_id, query_type, query_params)
            VALUES (?, ?, ?)
            ''', (user_id, query_type, str(query_params) if query_params else None))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"記錄查詢錯誤: {e}")
            return False

    # ========== 管理員功能 ==========
    
    def get_all_users(self):
        """獲取所有用戶（管理員功能）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, email, membership_level, created_at, last_login, is_active, is_admin
            FROM users ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'email': row[1],
                    'membership_level': row[2],
                    'created_at': row[3],
                    'last_login': row[4],
                    'is_active': bool(row[5]),
                    'is_admin': bool(row[6])
                })
            
            conn.close()
            return {'success': True, 'users': users}
            
        except Exception as e:
            return {'success': False, 'message': f'獲取用戶列表失敗: {str(e)}'}

    def update_user_membership(self, user_id, new_membership_level):
        """更新用戶會員等級（管理員功能）"""
        try:
            valid_levels = ['basic', 'premium', 'super']
            if new_membership_level not in valid_levels:
                return {'success': False, 'message': '無效的會員等級'}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE users SET membership_level = ? WHERE id = ?
            ''', (new_membership_level, user_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'message': '用戶不存在'}
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '會員等級更新成功'}
            
        except Exception as e:
            return {'success': False, 'message': f'更新會員等級失敗: {str(e)}'}

    def deactivate_user(self, user_id):
        """停用用戶（管理員功能）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'message': '用戶不存在'}
            
            # 清除該用戶的所有會話
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '用戶已停用'}
            
        except Exception as e:
            return {'success': False, 'message': f'停用用戶失敗: {str(e)}'}

    def activate_user(self, user_id):
        """啟用用戶（管理員功能）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'message': '用戶不存在'}
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '用戶已啟用'}
            
        except Exception as e:
            return {'success': False, 'message': f'啟用用戶失敗: {str(e)}'}

    def get_user_query_stats(self, user_id):
        """獲取用戶查詢統計（管理員功能）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 今日查詢次數
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
            SELECT COUNT(*) FROM query_logs 
            WHERE user_id = ? AND DATE(query_time) = ?
            ''', (user_id, today))
            today_queries = cursor.fetchone()[0]
            
            # 總查詢次數
            cursor.execute('SELECT COUNT(*) FROM query_logs WHERE user_id = ?', (user_id,))
            total_queries = cursor.fetchone()[0]
            
            # 最近查詢時間
            cursor.execute('''
            SELECT query_time FROM query_logs 
            WHERE user_id = ? ORDER BY query_time DESC LIMIT 1
            ''', (user_id,))
            last_query = cursor.fetchone()
            last_query_time = last_query[0] if last_query else None
            
            conn.close()
            
            return {
                'success': True,
                'stats': {
                    'today_queries': today_queries,
                    'total_queries': total_queries,
                    'last_query_time': last_query_time
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'獲取查詢統計失敗: {str(e)}'}

    def reset_user_password(self, user_id, new_password):
        """重置用戶密碼（管理員功能）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            
            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'message': '用戶不存在'}
            
            # 清除該用戶的所有會話，強制重新登入
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '密碼重置成功'}
            
        except Exception as e:
            return {'success': False, 'message': f'重置密碼失敗: {str(e)}'}

    def generate_random_password(self, length=8):
        """生成隨機密碼"""
        import string
        import random
        
        # 包含大小寫字母和數字
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(length))
        return password

    def forgot_password(self, email):
        """忘記密碼功能 - 生成隨機密碼並發送 email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 檢查用戶是否存在
            cursor.execute('SELECT id, email FROM users WHERE email = ? AND is_active = 1', (email,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {'success': False, 'message': '找不到此電子郵件的用戶'}
            
            user_id, user_email = user
            
            # 生成隨機密碼（8位英數字組合）
            new_password = self.generate_random_password()
            password_hash = self.hash_password(new_password)
            
            # 更新密碼
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            
            # 清除該用戶的所有會話，強制重新登入
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            # 發送 email（實際實現）
            email_sent = self.send_password_email(user_email, new_password)
            
            if email_sent:
                return {
                    'success': True, 
                    'message': f'新密碼已發送到您的信箱 {user_email}，請檢查您的電子郵件。',
                    'email_sent': True
                }
            else:
                # 如果 email 發送失敗，仍然返回密碼（備用方案）
                return {
                    'success': True, 
                    'message': f'密碼已重設，但 email 發送失敗。您的新密碼是：{new_password}',
                    'new_password': new_password,
                    'email_sent': False
                }
            
        except Exception as e:
            return {'success': False, 'message': f'重設密碼失敗: {str(e)}'}

    def send_password_email(self, email, password):
        """發送新密碼到用戶信箱 - 使用 SendGrid API"""
        try:
            from sendgrid_service import sendgrid_service
            
            # 使用 SendGrid 發送郵件
            result = sendgrid_service.send_password_reset_email(email, password)
            
            if result['success']:
                print(f"✅ SendGrid 郵件發送成功: {email}")
                return True
            else:
                print(f"❌ SendGrid 郵件發送失敗: {result['message']}")
                return False
                
        except Exception as e:
            print(f"SendGrid 發送異常: {e}")
            return False
