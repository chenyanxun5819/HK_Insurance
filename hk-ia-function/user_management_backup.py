import sqlite3
import hashlib
import secrets
from datetime import datetime, date
import os

class UserManager:
    def __init__(self, db_path='aml_profiles.db'):
        self.db_path = db_path
        self.init_user_tables()
    
        def check_query_limit(self, user_id):
        """檢查用戶查詢限制"""
        try:
            conn = sqlite3.connect(self.db_file)
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
            return {'allowed': False, 'message': '系統錯誤'}s(self):
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
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # 查詢記錄表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query_type TEXT,
            query_params TEXT,
            query_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """密碼哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_session_token(self):
        """生成會話token"""
        return secrets.token_urlsafe(32)
    
    def register_user(self, email, password):
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
            INSERT INTO users (email, password_hash, membership_level)
            VALUES (?, ?, ?)
            ''', (email, password_hash, 'basic'))
            
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
            SELECT id, email, membership_level FROM users 
            WHERE email = ? AND password_hash = ? AND is_active = 1
            ''', (email, password_hash))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return {'success': False, 'message': '帳號或密碼錯誤'}
            
            user_id, email, membership_level = user
            
            # 創建會話
            session_token = self.generate_session_token()
            expires_at = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)  # 當日結束
            
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
                    'membership_level': membership_level
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
            SELECT u.id, u.email, u.membership_level, s.expires_at
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND u.is_active = 1
            ''', (session_token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {'success': False, 'message': '無效的會話'}
            
            user_id, email, membership_level, expires_at = result
            expires_at = datetime.fromisoformat(expires_at)
            
            if datetime.now() > expires_at:
                return {'success': False, 'message': '會話已過期'}
            
            return {
                'success': True,
                'user': {
                    'id': user_id,
                    'email': email,
                    'membership_level': membership_level
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'會話驗證失敗: {str(e)}'}
    
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
    
    def log_query(self, user_id, query_type, query_params):
        """記錄查詢"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO query_logs (user_id, query_type, query_params, query_date)
            VALUES (?, ?, ?, ?)
            ''', (user_id, query_type, query_params, date.today()))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'message': f'記錄查詢失敗: {str(e)}'}
    
    def get_daily_query_count(self, user_id, query_date=None):
        """獲取用戶當日查詢次數"""
        if query_date is None:
            query_date = date.today()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM query_logs 
            WHERE user_id = ? AND query_date = ?
            ''', (user_id, query_date))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            return 0
    
    def check_query_limit(self, user_id, membership_level):
        """檢查查詢限制"""
        daily_count = self.get_daily_query_count(user_id)
        
        # 會員等級限制
        limits = {
            'basic': 5,
            'premium': 50,
            'unlimited': float('inf')
        }
        
        limit = limits.get(membership_level, 5)
        
        return {
            'can_query': daily_count < limit,
            'daily_count': daily_count,
            'daily_limit': limit,
            'remaining': max(0, limit - daily_count) if limit != float('inf') else float('inf')
        }
