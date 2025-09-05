#!/usr/bin/env python3
"""
AML 資料庫遷移腳本
從 SQLite 遷移 14,528+ 筆記錄到 Firestore
"""

import sqlite3
import os
import sys
from datetime import datetime
from google.cloud import firestore

class AMLDataMigrator:
    def __init__(self, use_emulator=True):
        """初始化遷移器"""
        self.use_emulator = use_emulator
        
        if use_emulator:
            print("🔄 連接到 Firestore 模擬器...")
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8081"
        else:
            print("🔄 連接到生產 Firestore...")
            
        self.db = firestore.Client(project="hk-insurance-crawler")
        self.collection_name = "aml_profiles"
        
        # SQLite 資料庫路徑
        self.sqlite_path = "/home/weschen/HK_insurance/aml_profiles.db"
        
    def get_sqlite_data(self):
        """從 SQLite 獲取所有資料"""
        print("📖 讀取 SQLite 資料...")
        
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # 獲取總數
        cursor.execute("SELECT COUNT(*) FROM profiles")
        total_count = cursor.fetchone()[0]
        print(f"📊 總記錄數: {total_count}")
        
        # 獲取所有資料
        cursor.execute("SELECT * FROM profiles")
        records = cursor.fetchall()
        
        # 獲取欄位名稱
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        return records, column_names, total_count
    
    def convert_record(self, record, column_names):
        """轉換記錄格式"""
        record_dict = dict(zip(column_names, record))
        
        # 轉換資料類型
        converted = {
            'id': str(record_dict['id']),  # Firestore 使用字串 ID
            'year': record_dict['year'],
            'name': record_dict['name'] or '',
            'nationality': record_dict['nationality'] or '',
            'passport_no': record_dict['passport_no'] or '',
            'source_pdf': record_dict['source_pdf'] or '',
            'source_url': record_dict['source_url'] or '',
            'created_at': record_dict['created_at'] or '',
            'migrated_at': datetime.utcnow().isoformat()
        }
        
        return converted
    
    def batch_upload(self, records, column_names, batch_size=500):
        """批次上傳資料到 Firestore"""
        total_records = len(records)
        print(f"🚀 開始批次上傳 {total_records} 筆記錄...")
        
        collection_ref = self.db.collection(self.collection_name)
        
        for i in range(0, total_records, batch_size):
            batch_records = records[i:i + batch_size]
            batch = self.db.batch()
            
            print(f"⬆️ 上傳批次 {i//batch_size + 1}: 記錄 {i+1}-{min(i+batch_size, total_records)}")
            
            for record in batch_records:
                converted = self.convert_record(record, column_names)
                doc_ref = collection_ref.document(converted['id'])
                batch.set(doc_ref, converted)
            
            # 執行批次寫入
            batch.commit()
            print(f"✅ 批次 {i//batch_size + 1} 完成")
        
        print(f"🎉 所有資料上傳完成！總共 {total_records} 筆記錄")
    
    def verify_migration(self, expected_count):
        """驗證遷移結果"""
        print("🔍 驗證遷移結果...")
        
        collection_ref = self.db.collection(self.collection_name)
        
        # 計算總數
        docs = collection_ref.stream()
        actual_count = sum(1 for _ in docs)
        
        print(f"📊 預期記錄數: {expected_count}")
        print(f"📊 實際記錄數: {actual_count}")
        
        if actual_count == expected_count:
            print("✅ 遷移驗證成功！所有記錄都已正確遷移")
            return True
        else:
            print(f"❌ 遷移驗證失敗！遺失 {expected_count - actual_count} 筆記錄")
            return False
    
    def get_sample_records(self, limit=5):
        """獲取範例記錄"""
        print(f"📝 獲取 {limit} 筆範例記錄...")
        
        collection_ref = self.db.collection(self.collection_name)
        docs = collection_ref.limit(limit).stream()
        
        for doc in docs:
            data = doc.to_dict()
            print(f"ID: {doc.id}")
            print(f"  姓名: {data.get('name', 'N/A')}")
            print(f"  國籍: {data.get('nationality', 'N/A')}")
            print(f"  年份: {data.get('year', 'N/A')}")
            print("---")
    
    def migrate(self):
        """執行完整遷移流程"""
        print("🚀 開始 AML 資料庫遷移...")
        print("=" * 50)
        
        try:
            # 1. 讀取 SQLite 資料
            records, column_names, total_count = self.get_sqlite_data()
            
            # 2. 批次上傳到 Firestore
            self.batch_upload(records, column_names)
            
            # 3. 驗證遷移結果
            success = self.verify_migration(total_count)
            
            # 4. 顯示範例記錄
            if success:
                self.get_sample_records()
            
            print("=" * 50)
            if success:
                print("🎉 AML 資料庫遷移完成！")
            else:
                print("❌ AML 資料庫遷移失敗！")
                
            return success
            
        except Exception as e:
            print(f"❌ 遷移過程發生錯誤: {str(e)}")
            return False

if __name__ == "__main__":
    print("AML 資料庫遷移工具")
    print("=" * 30)
    
    # 檢查模式
    use_emulator = True
    if len(sys.argv) > 1 and sys.argv[1] == "--production":
        use_emulator = False
        print("⚠️ 警告：將遷移到生產環境！")
        confirm = input("確定要繼續嗎？(yes/no): ")
        if confirm.lower() != 'yes':
            print("🛑 遷移已取消")
            sys.exit(0)
    
    # 執行遷移
    migrator = AMLDataMigrator(use_emulator=use_emulator)
    success = migrator.migrate()
    
    sys.exit(0 if success else 1)
