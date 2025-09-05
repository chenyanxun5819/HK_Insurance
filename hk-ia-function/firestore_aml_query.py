#!/usr/bin/env python3
"""
Firestore 版本的 AML 查詢引擎
"""

import os
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
import math

class FirestoreAMLQuery:
    def __init__(self, use_emulator=True):
        """初始化 Firestore AML 查詢引擎"""
        if use_emulator:
            os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8081"
            
        self.db = firestore.Client(project="hk-insurance-crawler")
        self.collection_name = "aml_profiles"
        
    def search_by_name(self, name, page=1, per_page=20):
        """按姓名搜尋 AML 記錄"""
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # Firestore 不支援 LIKE 查詢，需要使用不同策略
            # 我們使用 array-contains 和前綴匹配的組合
            
            # 先獲取所有符合條件的記錄（簡化版本，實際應該使用索引）
            all_docs = collection_ref.stream()
            
            # 客戶端過濾（注意：這不是最佳解決方案，但能正常工作）
            matches = []
            for doc in all_docs:
                data = doc.to_dict()
                if name.lower() in data.get('name', '').lower():
                    # 添加文檔 ID
                    data['firestore_id'] = doc.id
                    matches.append(data)
            
            # 計算分頁
            total = len(matches)
            total_pages = math.ceil(total / per_page) if total > 0 else 0
            
            # 分頁處理
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_matches = matches[start_idx:end_idx]
            
            return {
                "found": total > 0,
                "matches": page_matches,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
            
        except Exception as e:
            raise Exception(f"Firestore 查詢失敗: {str(e)}")
    
    def get_profiles_paginated(self, page=1, per_page=50, nationality=None):
        """分頁獲取 AML 記錄"""
        try:
            collection_ref = self.db.collection(self.collection_name)
            
            # 構建查詢
            query = collection_ref
            
            # 如果有國籍過濾條件
            if nationality:
                # 使用客戶端過濾（Firestore 的字串匹配限制）
                all_docs = collection_ref.stream()
                filtered_docs = []
                
                for doc in all_docs:
                    data = doc.to_dict()
                    if nationality.lower() in data.get('nationality', '').lower():
                        data['firestore_id'] = doc.id
                        filtered_docs.append(data)
                
                # 計算分頁
                total = len(filtered_docs)
                total_pages = math.ceil(total / per_page) if total > 0 else 0
                
                # 分頁處理
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                page_docs = filtered_docs[start_idx:end_idx]
                
            else:
                # 無過濾條件，直接分頁
                # 先獲取總數（注意：這是昂貴的操作）
                all_docs = list(collection_ref.stream())
                total = len(all_docs)
                total_pages = math.ceil(total / per_page) if total > 0 else 0
                
                # 分頁處理
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                page_docs = []
                
                for i, doc in enumerate(all_docs[start_idx:end_idx]):
                    data = doc.to_dict()
                    data['firestore_id'] = doc.id
                    page_docs.append(data)
            
            return {
                "success": True,
                "profiles": page_docs,
                "total_profiles": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"獲取資料失敗: {str(e)}",
                "profiles": [],
                "total_profiles": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0
            }
    
    def get_stats(self):
        """獲取統計資訊 - 與前端格式匹配"""
        try:
            collection_ref = self.db.collection(self.collection_name)
            docs = list(collection_ref.stream())
            
            total_profiles = len(docs)
            
            # 按年份統計
            year_stats = {}
            
            for doc in docs:
                data = doc.to_dict()
                year = data.get('year')
                if year:
                    year_stats[year] = year_stats.get(year, 0) + 1
            
            # 轉換為前端期望的格式
            year_stats_list = [
                {"year": year, "count": count} 
                for year, count in sorted(year_stats.items(), reverse=True)
            ]
            
            return {
                "total_profiles": total_profiles,
                "year_stats": year_stats_list
            }
            
        except Exception as e:
            return {
                "error": f"統計查詢失敗: {str(e)}",
                "total_profiles": 0,
                "year_stats": []
            }
