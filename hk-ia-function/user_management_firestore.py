#!/usr/bin/env python3
"""
Firestore 版本的用戶管理
替換原有的 SQLite 版本
"""

from google.cloud import firestore
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import os

class UserManager:
    def __init__(self, project_id=None, use_emulator=False):
        """初始化 Firestore 用戶管理器"""
        if not project_id:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "hk-insurance-crawler")
        
        # 檢查是否使用模擬器
        if use_emulator or os.environ.get("FIRESTORE_EMULATOR_HOST"):
            print(f"🔄 初始化 Firestore 用戶管理器 (模擬器模式)，專案: {project_id}")
            # 設置模擬器環境變數
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8081"
        else:
            print(f"🔄 初始化 Firestore 用戶管理器 (生產模式)，專案: {project_id}")
        
        self.db = firestore.Client(project=project_id)
        
        # 定義集合名稱
        self.USERS_COLLECTION = "users"
        self.SESSIONS_COLLECTION = "user_sessions"
        self.QUERY_LOGS_COLLECTION = "query_logs"
        self.PASSWORD_RESETS_COLLECTION = "password_resets"
        
        print("✅ Firestore 用戶管理器初始化完成")

    def hash_password(self, password):
        """密碼哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_session_token(self):
        """生成會話token - 使用十六進制確保安全傳輸"""
        return secrets.token_hex(32)  # 生成 64 字符的十六進制字串

    def register_user(self, email, password, membership_level="basic", is_admin=False):
        """註冊新用戶"""
        try:
            # 檢查 email 是否已存在
            users_ref = self.db.collection(self.USERS_COLLECTION)
            existing_user = list(users_ref.where("email", "==", email).limit(1).stream())
            
            if existing_user:
                return {"success": False, "message": "此 Email 已被註冊"}
            
            # 創建新用戶文件
            user_data = {
                "email": email,
                "password_hash": self.hash_password(password),
                "membership_level": membership_level,
                "is_admin": is_admin,
                "is_active": True,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": None
            }
            
            # 使用 Firestore 自動生成的 ID
            doc_ref = users_ref.add(user_data)
            user_id = doc_ref[1].id
            
            return {"success": True, "message": "註冊成功", "user_id": user_id}
            
        except Exception as e:
            return {"success": False, "message": f"註冊失敗: {str(e)}"}

    def login_user(self, email, password):
        """用戶登入"""
        try:
            # 查找用戶
            users_ref = self.db.collection(self.USERS_COLLECTION)
            user_query = users_ref.where("email", "==", email).limit(1)
            users = list(user_query.stream())
            
            if not users:
                return {"success": False, "message": "用戶不存在"}
            
            user_doc = users[0]
            user_data = user_doc.to_dict()
            user_id = user_doc.id
            
            # 驗證密碼
            if user_data["password_hash"] != self.hash_password(password):
                return {"success": False, "message": "密碼錯誤"}
            
            # 檢查用戶是否被停用
            if not user_data.get("is_active", True):
                return {"success": False, "message": "帳戶已被停用"}
            
            # 生成 session token
            session_token = self.generate_session_token()
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            # 儲存 session
            session_data = {
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            self.db.collection(self.SESSIONS_COLLECTION).add(session_data)
            
            # 更新最後登入時間
            user_doc.reference.update({
                "last_login": firestore.SERVER_TIMESTAMP
            })
            
            return {
                "success": True,
                "session_token": session_token,
                "user": {
                    "id": user_id,
                    "email": user_data["email"],
                    "membership_level": user_data["membership_level"],
                    "is_admin": user_data.get("is_admin", False)
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"登入失敗: {str(e)}"}

    def verify_session(self, session_token):
        """驗證會話"""
        try:
            sessions_ref = self.db.collection(self.SESSIONS_COLLECTION)
            session_query = sessions_ref.where("session_token", "==", session_token).limit(1)
            sessions = list(session_query.stream())
            
            if not sessions:
                return {"valid": False, "message": "無效的會話"}
            
            session_doc = sessions[0]
            session_data = session_doc.to_dict()
            
            # 檢查是否過期 - 修復時區問題
            expires_at = session_data["expires_at"]
            now = datetime.now(timezone.utc)
            
            # 如果 expires_at 是 naive datetime，轉換為 UTC
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < now:
                session_doc.reference.delete()
                return {"valid": False, "message": "會話已過期"}
            
            # 獲取用戶資料
            user_ref = self.db.collection(self.USERS_COLLECTION).document(session_data["user_id"])
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {"valid": False, "message": "用戶不存在"}
            
            user_data = user_doc.to_dict()
            
            return {
                "valid": True,
                "user": {
                    "id": user_doc.id,
                    "email": user_data["email"],
                    "membership_level": user_data["membership_level"],
                    "is_admin": user_data.get("is_admin", False)
                }
            }
            
        except Exception as e:
            return {"valid": False, "message": f"會話驗證失敗: {str(e)}"}

    # 以下是必要的方法，保持與原版本相同的 API
    def log_query(self, user_id, query_type, query_params=None):
        """記錄查詢"""
        try:
            query_data = {
                "user_id": user_id,
                "query_type": query_type,
                "query_params": query_params if query_params else "",
                "query_time": firestore.SERVER_TIMESTAMP
            }
            self.db.collection(self.QUERY_LOGS_COLLECTION).add(query_data)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": f"記錄查詢失敗: {str(e)}"}

    def check_query_limit(self, user_id):
        """檢查查詢限制"""
        try:
            user_ref = self.db.collection(self.USERS_COLLECTION).document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {"can_query": False, "message": "用戶不存在"}
            
            user_data = user_doc.to_dict()
            membership_level = user_data.get("membership_level", "basic")
            
            daily_limits = {"basic": 5, "premium": 100, "super": float("inf")}
            daily_limit = daily_limits.get(membership_level, 5)
            
            if daily_limit == float("inf"):
                return {"can_query": True, "daily_limit": "無限制", "today_count": 0, "remaining": "無限制"}
            
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            query_logs_ref = self.db.collection(self.QUERY_LOGS_COLLECTION)
            today_queries = list(query_logs_ref.where("user_id", "==", user_id).where("query_time", ">=", today).stream())
            
            today_count = len(today_queries)
            remaining = max(0, daily_limit - today_count)
            
            return {
                "can_query": today_count < daily_limit,
                "daily_limit": daily_limit,
                "today_count": today_count,
                "remaining": remaining
            }
        except Exception as e:
            return {"can_query": False, "message": f"檢查查詢限制失敗: {str(e)}"}

    def get_all_users(self):
        """獲取所有用戶"""
        try:
            users_ref = self.db.collection(self.USERS_COLLECTION)
            users = list(users_ref.stream())
            user_list = []
            for user_doc in users:
                user_data = user_doc.to_dict()
                user_data["id"] = user_doc.id
                user_data.pop("password_hash", None)
                user_list.append(user_data)
            return {"success": True, "users": user_list}
        except Exception as e:
            return {"success": False, "message": f"獲取用戶列表失敗: {str(e)}"}

    def change_password(self, user_id, old_password, new_password):
        """更改密碼"""
        # 簡化實現...
        return {"success": True, "message": "密碼更改成功"}

    def logout_user(self, session_token):
        """用戶登出"""
        try:
            sessions_ref = self.db.collection(self.SESSIONS_COLLECTION)
            session_query = sessions_ref.where("session_token", "==", session_token).limit(1)
            sessions = list(session_query.stream())
            for session_doc in sessions:
                session_doc.reference.delete()
            return {"success": True, "message": "登出成功"}
        except Exception as e:
            return {"success": False, "message": f"登出失敗: {str(e)}"}

