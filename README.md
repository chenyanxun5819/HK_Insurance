# HK Insurance AML 制裁名單查詢系統

## 專案概述
香港保險業監管局 (IA) 反洗錢制裁名單查詢系統，支援快速搜尋和瀏覽制裁名單資料。

## 現狀 (2025年9月)
✅ **已完成功能**：
- **Firestore 遷移**：成功遷移 14,528 筆 AML 制裁名單資料
- **基本查詢功能**：姓名搜尋、分頁瀏覽、統計資訊
- **Firebase 模擬器支援**：本地開發環境
- **簡化存取**：移除認證要求，直接查詢
- **響應式界面**：現代化的 Web 前端

## 技術架構
- **後端**：Python Flask + Google Firestore
- **前端**：HTML5 + JavaScript + 響應式 CSS
- **資料庫**：Google Firestore (雲端 NoSQL)
- **部署**：支援 Firebase 模擬器開發環境

## 分支說明
- **master**：初步查詢基本功能 (穩定版本)
- **更新2025資料**：即將新增 2025 年最新制裁資料

## 快速開始

### 環境設置
```bash
# 安裝依賴
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r hk-ia-function/requirements.txt

# 啟動 Firebase 模擬器
firebase emulators:start

# 啟動 Flask 應用
cd hk-ia-function
python main.py
```

### 訪問應用
- **查詢界面**：http://127.0.0.1:8000
- **Firebase 控制台**：http://127.0.0.1:4000

## 資料統計
- **總記錄數**：14,528 筆
- **涵蓋年份**：2001-2024
- **資料來源**：香港保險業監管局官方通告

## 主要文件
- `hk-ia-function/main.py`：主應用程式
- `hk-ia-function/firestore_aml_query.py`：Firestore 查詢引擎
- `migrate_aml_data.py`：資料遷移腳本
- `firebase.json`：Firebase 配置

## 未來計劃
- [ ] 新增 2025 年制裁資料
- [ ] 優化查詢性能
- [ ] 增加資料匯出功能
- [ ] 支援多語言界面

## 開發者
- 初步開發：2024-2025
- 主要功能：AML 制裁名單查詢系統
- 技術支援：Firebase + Flask 架構
