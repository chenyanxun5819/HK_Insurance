#!/usr/bin/env python3
"""
資料遷移腳本：從 SQLite 遷移 AML 資料到 Firestore
"""

import os
import sqlite3
from google.cloud import firestore
import json
from datetime import datetime

def migrate_sqlite_to_firestore():
    """將 SQLite 中的 AML 資料遷移到 Firestore"""
    
    # 設置模擬器環境
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8081"
    
    # 初始化 Firestore
    db = firestore.Client(project="hk-insurance-crawler")
    collection_name = "aml_profiles"
    
    # 連接 SQLite
    sqlite_db = "aml_profiles.db"
    conn = sqlite3.connect(sqlite_db)
    conn.row_factory = sqlite3.Row
    
    try:
        print("🔄 開始資料遷移...")
        
        # 清空 Firestore 集合（如果存在）
        collection_ref = db.collection(collection_name)
        
        # 刪除現有資料
        docs = collection_ref.limit(10).stream()
        delete_count = 0
        for doc in docs:
            doc.reference.delete()
            delete_count += 1
        
        if delete_count > 0:
            print(f"🗑️ 已清理 {delete_count} 條現有記錄")
        
        # 從 SQLite 讀取資料
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles")
        
        batch_size = 500
        batch = db.batch()
        batch_count = 0
        total_migrated = 0
        
        for row in cursor.fetchall():
            # 轉換 SQLite 記錄為 Firestore 文檔
            doc_data = {
                'name': row['name'] or '',
                'nationality': row['nationality'] or '',
                'passport': row['passport'] or '',
                'id_number': row['id_number'] or '',
                'date_of_birth': row['date_of_birth'] or '',
                'place_of_birth': row['place_of_birth'] or '',
                'address': row['address'] or '',
                'designation': row['designation'] or '',
                'other_information': row['other_information'] or '',
                'listed_on': row['listed_on'] or '',
                'source_url': row['source_url'] or '',
                'additional_info': row['additional_info'] or '',
                'migrated_at': firestore.SERVER_TIMESTAMP,
                'source': 'sqlite_migration'
            }
            
            # 添加到批次
            doc_ref = collection_ref.document()
            batch.set(doc_ref, doc_data)
            batch_count += 1
            
            # 每 500 條記錄提交一次
            if batch_count >= batch_size:
                batch.commit()
                total_migrated += batch_count
                print(f"✅ 已遷移 {total_migrated} 條記錄...")
                
                # 重置批次
                batch = db.batch()
                batch_count = 0
        
        # 提交剩餘的記錄
        if batch_count > 0:
            batch.commit()
            total_migrated += batch_count
        
        print(f"🎉 資料遷移完成！總共遷移了 {total_migrated} 條記錄")
        
        # 驗證遷移結果
        verify_migration(db, collection_name, total_migrated)
        
    except Exception as e:
        print(f"❌ 遷移失敗: {str(e)}")
        raise
    finally:
        conn.close()

def verify_migration(db, collection_name, expected_count):
    """驗證遷移結果"""
    try:
        # 統計 Firestore 中的記錄數
        collection_ref = db.collection(collection_name)
        docs = list(collection_ref.stream())
        actual_count = len(docs)
        
        print(f"📊 驗證結果:")
        print(f"   預期記錄數: {expected_count}")
        print(f"   實際記錄數: {actual_count}")
        
        if actual_count == expected_count:
            print("✅ 遷移驗證成功！")
        else:
            print("⚠️ 記錄數不匹配，請檢查遷移過程")
            
        # 顯示一個範例記錄
        if docs:
            sample_doc = docs[0]
            print(f"📝 範例記錄: {sample_doc.to_dict()}")
            
    except Exception as e:
        print(f"❌ 驗證失敗: {str(e)}")

if __name__ == "__main__":
    migrate_sqlite_to_firestore()
