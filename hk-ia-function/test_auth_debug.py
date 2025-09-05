#!/usr/bin/env python3
"""
測試認證系統和管理員功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_management import UserManager

def test_authentication():
    print("🔐 測試認證系統...")
    
    # 初始化用戶管理器
    user_manager = UserManager()
    
    # 測試用戶
    test_email = "astcws@hotmail.com"
    
    print(f"\n📧 測試帳戶: {test_email}")
    
    # 檢查用戶是否存在
    import sqlite3
    conn = sqlite3.connect(user_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT email, membership_level, is_admin, is_active FROM users WHERE email = ?", (test_email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        print(f"✅ 用戶存在: {user}")
        email, membership, is_admin, is_active = user
        print(f"   - 會員等級: {membership}")
        print(f"   - 是否管理員: {'是' if is_admin else '否'}")
        print(f"   - 帳戶狀態: {'啟用' if is_active else '停用'}")
    else:
        print("❌ 用戶不存在")
        return
    
    # 測試密碼重置 token
    print(f"\n🔑 生成密碼重置 token...")
    reset_result = user_manager.create_reset_token(test_email)
    if reset_result['success']:
        print(f"✅ 重置 token 已生成")
        token = reset_result['reset_token']
        print(f"   Token: {token[:20]}...")
        
        # 測試新密碼設置
        new_password = "TestPassword123!"
        reset_password_result = user_manager.reset_password(token, new_password)
        if reset_password_result['success']:
            print(f"✅ 密碼重置成功")
            
            # 測試登入
            print(f"\n🚪 測試登入...")
            login_result = user_manager.login_user(test_email, new_password)
            if login_result['success']:
                print(f"✅ 登入成功")
                session_token = login_result['session_token']
                print(f"   Session: {session_token[:20]}...")
                
                # 測試 session 驗證
                print(f"\n🔍 測試 session 驗證...")
                verify_result = user_manager.verify_session(session_token)
                if verify_result['valid']:
                    print(f"✅ Session 驗證成功")
                    user_info = verify_result['user']
                    print(f"   用戶: {user_info['email']}")
                    print(f"   管理員: {'是' if user_info['is_admin'] else '否'}")
                else:
                    print(f"❌ Session 驗證失敗: {verify_result['message']}")
            else:
                print(f"❌ 登入失敗: {login_result['message']}")
        else:
            print(f"❌ 密碼重置失敗: {reset_password_result['message']}")
    else:
        print(f"❌ 重置 token 生成失敗: {reset_result['message']}")

if __name__ == "__main__":
    test_authentication()
