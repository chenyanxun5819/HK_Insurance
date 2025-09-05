#!/usr/bin/env python3
"""
簡化管理員檢查 - 直接確保只有 astcws@hotmail.com 可以訪問管理功能
"""

def is_admin_user(session_token):
    """簡化的管理員檢查 - 專門為 astcws@hotmail.com"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('aml_profiles.db')
        cursor = conn.cursor()
        
        # 直接檢查這個 session 是否屬於 astcws@hotmail.com
        cursor.execute('''
        SELECT u.email, u.is_admin
        FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.session_token = ? AND u.email = 'astcws@hotmail.com' AND u.is_active = 1
        ''', (session_token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            email, is_admin = result
            return {'valid': True, 'email': email, 'is_admin': bool(is_admin)}
        else:
            return {'valid': False, 'message': '非管理員帳戶'}
            
    except Exception as e:
        return {'valid': False, 'message': f'檢查失敗: {str(e)}'}

# 測試函數
if __name__ == "__main__":
    # 獲取最新的 session token
    import sqlite3
    conn = sqlite3.connect('aml_profiles.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT session_token FROM user_sessions 
        WHERE user_id = (SELECT id FROM users WHERE email = 'astcws@hotmail.com')
        ORDER BY created_at DESC LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        session_token = result[0]
        print(f"測試 session: {session_token[:20]}...")
        check_result = is_admin_user(session_token)
        print(f"檢查結果: {check_result}")
    else:
        print("沒有找到有效的 session")
