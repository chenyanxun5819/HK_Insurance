#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建立會員系統資料庫結構
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta

def create_database():
    """建立會員系統資料庫"""
    conn = sqlite3.connect('/home/weschen/HK_insurance/members.db')
    cursor = conn.cursor()
    
    # 建立用戶表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'basic',  -- admin, paid, basic
        status TEXT NOT NULL DEFAULT 'active',  -- active, suspended, deleted
        query_limit INTEGER NOT NULL DEFAULT 5,
        queries_used INTEGER NOT NULL DEFAULT 0,
        email_verified INTEGER NOT NULL DEFAULT 0,
        failed_login_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        last_login_at TEXT,
        last_login_ip TEXT,
        expire_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # 建立查詢紀錄表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS query_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        result_count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 建立密碼重設表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # 建立 Email 驗證表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0
    )
    ''')
    
    # 建立付費紀錄表（預留）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        plan TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 插入管理員帳號
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    current_time = datetime.now().isoformat()
    
    cursor.execute('''
    INSERT OR REPLACE INTO users 
    (email, password_hash, role, status, query_limit, queries_used, email_verified, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'astcws@hotmail',
        admin_password,
        'admin',
        'active',
        -1,  # 無限制
        0,
        1,   # 已驗證
        current_time,
        current_time
    ))
    
    conn.commit()
    conn.close()
    print("✅ 會員資料庫建立完成")
    print("👤 管理員帳號: astcws@hotmail")
    print("🔑 管理員密碼: admin123")

if __name__ == '__main__':
    create_database()
