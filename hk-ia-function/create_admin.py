#!/usr/bin/env python3
"""
Firestore 版本的管理員創建腳本
"""

def create_admin_if_not_exists(user_manager):
    """確保管理員帳戶存在"""
    try:
        admin_email = "astcws@gmail.com"
        admin_password = "admin123"
        
        print(f"🔍 檢查管理員帳戶: {admin_email}")
        
        # 嘗試註冊管理員帳戶
        result = user_manager.register_user(
            email=admin_email,
            password=admin_password,
            membership_level='super',
            is_admin=True
        )
        
        if result['success']:
            print(f"✅ 成功創建管理員帳戶: {admin_email}")
        else:
            print(f"ℹ️ 註冊結果: {result['message']}")
            
            # 嘗試登入確認帳戶存在且可用
            login_result = user_manager.login_user(admin_email, admin_password)
            if login_result['success']:
                print(f"✅ 管理員帳戶已存在且可正常登入")
            else:
                print(f"❌ 管理員帳戶登入失敗: {login_result['message']}")
            
    except Exception as e:
        print(f"❌ 管理員帳戶處理失敗: {str(e)}")
        pass
