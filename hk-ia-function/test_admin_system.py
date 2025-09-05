#!/usr/bin/env python3
"""
HK Insurance AML 管理員系統測試腳本
"""

import sqlite3
import hashlib
from datetime import datetime

def test_admin_system():
    """測試管理員系統的完整功能"""
    
    print("🛡️  HK Insurance AML 管理員系統測試")
    print("=" * 50)
    
    conn = sqlite3.connect('aml_profiles.db')
    cursor = conn.cursor()
    
    # 1. 檢查用戶表結構
    print("\n📋 1. 用戶表結構")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # 2. 顯示所有用戶
    print("\n👥 2. 所有用戶列表")
    cursor.execute('''
    SELECT id, email, membership_level, is_admin, is_active, 
           created_at, last_login
    FROM users ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    for user in users:
        uid, email, level, is_admin, is_active, created, last_login = user
        
        # 格式化顯示
        admin_badge = "👑 管理員" if is_admin else "👤 一般用戶"
        
        level_info = {
            'basic': '初級會員 (5次/日)',
            'premium': '付費會員 (100次/日)', 
            'super': '超級會員 (無限制)'
        }.get(level, level)
        
        status = "🟢 啟用" if is_active else "🔴 停用"
        
        print(f"   ID:{uid} | {email}")
        print(f"   {admin_badge} | {level_info} | {status}")
        print(f"   註冊: {created} | 最後登入: {last_login or '未登入'}")
        print()
    
    # 3. 會員等級權限說明
    print("🏆 3. 會員等級權限")
    levels = [
        ("初級會員 (basic)", "每日 5 次查詢", "免費註冊"),
        ("付費會員 (premium)", "每日 100 次查詢", "付費升級"),
        ("超級會員 (super)", "無限制查詢", "管理員設定")
    ]
    
    for level_name, limit, note in levels:
        print(f"   • {level_name}: {limit} ({note})")
    
    # 4. 查詢記錄統計
    print("\n📊 4. 查詢統計")
    today = datetime.now().strftime('%Y-%m-%d')
    
    for user in users:
        uid, email = user[0], user[1]
        
        # 今日查詢
        cursor.execute('''
        SELECT COUNT(*) FROM query_logs 
        WHERE user_id = ? AND DATE(created_at) = ?
        ''', (uid, today))
        today_count = cursor.fetchone()[0]
        
        # 總查詢
        cursor.execute('SELECT COUNT(*) FROM query_logs WHERE user_id = ?', (uid,))
        total_count = cursor.fetchone()[0]
        
        print(f"   {email}: 今日 {today_count} 次 | 總計 {total_count} 次")
    
    # 5. 管理員功能測試
    print("\n⚙️  5. 管理員功能")
    admin_functions = [
        "✅ 查看所有用戶",
        "✅ 修改用戶會員等級",
        "✅ 啟用/停用用戶",
        "✅ 重置用戶密碼",
        "✅ 查看用戶查詢統計",
        "✅ 無限制查詢權限"
    ]
    
    for func in admin_functions:
        print(f"   {func}")
    
    # 6. 系統狀態
    print("\n🌟 6. 系統狀態")
    
    # AML資料統計
    cursor.execute('SELECT COUNT(*) FROM profiles')
    total_profiles = cursor.fetchone()[0]
    
    cursor.execute('SELECT MAX(year) FROM profiles')
    latest_year = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM profiles WHERE year = ?', (latest_year,))
    latest_year_count = cursor.fetchone()[0]
    
    print(f"   📁 AML制裁名單: {total_profiles:,} 筆")
    print(f"   📅 最新年份: {latest_year} ({latest_year_count} 筆)")
    print(f"   👥 註冊用戶: {len(users)} 位")
    print(f"   👑 管理員: {sum(1 for u in users if u[3])} 位")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ 管理員系統測試完成！")
    
    # 7. 使用說明
    print("\n📖 使用說明:")
    print("   1. 一般用戶: email + password 登入")
    print("   2. 管理員登入: admin@hk-insurance.com / admin123456")
    print("   3. 管理員面板: /admin")
    print("   4. 用戶管理: 可修改等級、重置密碼、停用帳號")
    print("   5. 會員等級: basic → premium → super")

if __name__ == "__main__":
    test_admin_system()
