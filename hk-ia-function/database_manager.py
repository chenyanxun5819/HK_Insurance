#!/usr/bin/env python3
"""
Google Cloud Storage 資料庫備份方案
在容器啟動時下載資料庫，關閉時上傳
"""

import os
import sqlite3
from google.cloud import storage
import atexit
import signal
import sys

class DatabaseManager:
    def __init__(self, bucket_name, db_filename="aml_profiles.db"):
        self.bucket_name = bucket_name
        self.db_filename = db_filename
        self.local_db_path = f"/app/{db_filename}"
        self.storage_client = storage.Client()
        
        # 註冊關閉時的清理函數
        atexit.register(self.upload_database)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """處理關閉信號"""
        print(f"收到關閉信號 {signum}，上傳資料庫...")
        self.upload_database()
        sys.exit(0)
        
    def download_database(self):
        """從 Cloud Storage 下載資料庫"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.db_filename)
            
            if blob.exists():
                print(f"📥 從 Cloud Storage 下載資料庫: {self.db_filename}")
                blob.download_to_filename(self.local_db_path)
                print("✅ 資料庫下載完成")
            else:
                print(f"ℹ️ Cloud Storage 中沒有現有資料庫，將創建新的")
                self.create_new_database()
                
        except Exception as e:
            print(f"❌ 下載資料庫失敗: {str(e)}")
            print("🔄 創建新資料庫...")
            self.create_new_database()
            
    def create_new_database(self):
        """創建新的資料庫文件"""
        # 這裡可以運行初始化腳本
        conn = sqlite3.connect(self.local_db_path)
        conn.close()
        print(f"✅ 創建新資料庫: {self.local_db_path}")
        
    def upload_database(self, immediate=False):
        """上傳資料庫到 Cloud Storage
        Args:
            immediate: 是否為即時備份（用於專家建議的立即備份）
        """
        try:
            if os.path.exists(self.local_db_path):
                bucket = self.storage_client.bucket(self.bucket_name)
                blob = bucket.blob(self.db_filename)
                
                backup_type = "即時備份" if immediate else "定期備份"
                print(f"📤 {backup_type}資料庫到 Cloud Storage: {self.db_filename}")
                blob.upload_from_filename(self.local_db_path)
                print(f"✅ {backup_type}上傳完成")
            else:
                print("⚠️ 本地資料庫文件不存在，跳過上傳")
                
        except Exception as e:
            print(f"❌ 上傳資料庫失敗: {str(e)}")
            
    def immediate_backup(self):
        """立即備份（專家建議的寫入後立即備份）"""
        self.upload_database(immediate=True)
            
    def get_db_path(self):
        """獲取本地資料庫路徑"""
        return self.local_db_path

# 使用範例
if __name__ == "__main__":
    # 初始化資料庫管理器
    db_manager = DatabaseManager("hk-ia-db", "aml_profiles.db")
    
    # 啟動時下載資料庫
    db_manager.download_database()
    
    print(f"資料庫路徑: {db_manager.get_db_path()}")
