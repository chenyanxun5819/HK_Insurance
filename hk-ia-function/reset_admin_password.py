#!/usr/bin/env python3
"""
簡化的管理員密碼設置腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_management import UserManager
import sqlite3

def reset_admin_password():
    print("🔐 重置管理員密碼...")
    
    user_manager = UserManager()
    admin_email = "astcws@hotmail.com"
    new_password = "admin123"  # 簡單的測試密碼
    
    # 直接重置密碼
    result = user_manager.reset_user_password_by_email(admin_email, new_password)
    
    if result['success']:
        print(f"✅ 密碼重置成功")
        print(f"   帳戶: {admin_email}")
        print(f"   新密碼: {new_password}")
        
        # 測試登入
        print(f"\n🚪 測試登入...")
        login_result = user_manager.login_user(admin_email, new_password)
        if login_result['success']:
            print(f"✅ 登入成功")
            print(f"   Session: {login_result['session_token'][:20]}...")
            print(f"   會員等級: {login_result['user']['membership_level']}")
            print(f"   管理員權限: {'是' if login_result['user']['is_admin'] else '否'}")
        else:
            print(f"❌ 登入失敗: {login_result['message']}")
    else:
        print(f"❌ 密碼重置失敗: {result['message']}")

# 添加重置密碼方法到 UserManager
def add_reset_method():
    # 直接在資料庫中重置密碼
    import hashlib
    
    user_manager = UserManager()
    admin_email = "astcws@hotmail.com"
    new_password = "admin123"
    
    # 生成密碼哈希
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # 更新資料庫
    conn = sqlite3.connect(user_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE email = ?
    """, (password_hash, admin_email))
    
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    
    if rows_affected > 0:
        print(f"✅ 密碼已直接更新在資料庫中")
        print(f"   帳戶: {admin_email}")
        print(f"   新密碼: {new_password}")
        
        # 測試登入
        print(f"\n🚪 測試登入...")
        login_result = user_manager.login_user(admin_email, new_password)
        if login_result['success']:
            print(f"✅ 登入成功")
        else:
            print(f"❌ 登入失敗: {login_result['message']}")
    else:
        print(f"❌ 沒有找到用戶或更新失敗")

if __name__ == "__main__":
    add_reset_method()
