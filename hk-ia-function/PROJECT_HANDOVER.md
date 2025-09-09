# 香港保險監管局 AML 查詢系統 - 專案交接文檔

## 📋 專案概述

這是一個基於 Flask 的香港保險監管局 AML (反洗錢) 查詢系統，提供完整的會員管理和 PDF 文檔查詢功能。

### 核心功能
- **會員系統**：註冊、登入、密碼重置、管理員功能
- **AML 查詢**：PDF 文檔內容搜尋和顯示
- **管理員面板**：會員管理、系統監控
- **郵件服務**：SendGrid 集成的郵件驗證和通知

## 🏗️ 技術架構

### 前端
- **模板引擎**：Jinja2
- **CSS 框架**：Bootstrap 5
- **JavaScript**：原生 JS + 部分 jQuery

### 後端
- **框架**：Flask 2.x
- **數據庫**：SQLite (本地開發)
- **郵件服務**：SendGrid API
- **認證**：Flask-Login + 自定義會員系統

### 關鍵檔案結構
```
/home/weschen/HK_insurance/hk-ia-function/
├── main_full.py              # 主要 Flask 應用（當前穩定版本）
├── user_management.py        # 會員管理模組
├── sendgrid_service.py       # 郵件服務模組
├── database_manager.py       # 數據庫管理
├── aml_profiles.db          # SQLite 數據庫
├── venv/                    # 虛擬環境
├── templates/               # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── member/             # 會員相關頁面
│   └── admin/              # 管理員頁面
└── requirements.txt         # Python 依賴清單
```

## 🚀 啟動指南

### 1. 環境設置
```bash
# 進入專案目錄
cd /home/weschen/HK_insurance/hk-ia-function

# 啟動虛擬環境
source venv/bin/activate

# 檢查依賴 (如需要)
pip install -r requirements.txt
```

### 2. 啟動服務
```bash
# 啟動 Flask 服務
python main_full.py
```

**正常啟動輸出：**
```
🚀 啟動完整會員制度 AML 查詢系統...
 * Running on http://127.0.0.1:5000
 * Debug mode: on
 * Debugger is active!
```

### 3. 訪問方式
- **主頁**：http://127.0.0.1:5000
- **登入**：http://127.0.0.1:5000/login
- **註冊**：http://127.0.0.1:5000/register
- **管理員**：http://127.0.0.1:5000/admin

## ⚠️ 已知問題和解決方案

### 1. 虛擬環境混淆問題
**問題**：母專案有 `.venv`，子專案有 `venv`，容易混淆
**解決**：建議只開啟子專案 `/home/weschen/HK_insurance/hk-ia-function`

### 2. Flask 服務自動終止
**症狀**：服務啟動後立即出現 `^C` 並終止
**解決**：確認使用正確的虛擬環境路徑，避免路徑衝突

### 3. 數據庫連接問題
**檢查**：確認 `aml_profiles.db` 文件存在且可讀寫
**位置**：`/home/weschen/HK_insurance/hk-ia-function/aml_profiles.db`

## 📧 郵件服務配置

### SendGrid 設置
- **API Key**：已配置在 `sendgrid_service.py`
- **發送者**：已設置驗證過的發送者地址
- **功能**：會員驗證、密碼重置、管理員通知

### 相關檔案
- `sendgrid_service.py` - 郵件服務主模組
- `SENDGRID_SETUP.md` - 詳細設置說明
- `EMAIL_SETUP.md` - 郵件配置指南

## 👤 會員系統

### 管理員功能
- **預設管理員**：admin / admin123
- **管理頁面**：/admin
- **功能**：會員列表、權限管理、系統監控

### 會員權限
- **一般會員**：查詢 AML 文檔
- **管理員**：完整系統管理權限

## 🐛 除錯指令

### 檢查服務狀態
```bash
# 檢查端口佔用
lsof -i:5000

# 測試連接
curl -I http://127.0.0.1:5000

# 檢查 Flask 應用載入
python -c "from main_full import app; print('App loaded successfully')"
```

### 數據庫操作
```bash
# 檢查數據庫
sqlite3 aml_profiles.db ".tables"

# 查看會員
sqlite3 aml_profiles.db "SELECT * FROM members LIMIT 5;"
```

## 📝 開發注意事項

### 1. 版本控制
- **Git 倉庫**：位於母專案 `/home/weschen/HK_insurance/.git`
- **分支**：當前在 `加上會員功能` 分支
- **提交**：可在子專案中正常使用 Git 命令

### 2. 檔案版本說明
- `main_full.py` - 當前穩定版本 ✅
- `main_simple.py` - 簡化版本
- `main_firebase.py` - Firebase 版本（已停用）
- `main_hybrid.py` - 混合版本

### 3. 環境變量
確認以下設置：
- **FLASK_ENV**: development
- **FLASK_DEBUG**: True
- **SECRET_KEY**: 已設置

## 🔧 故障排除

### 常見問題
1. **ImportError**: 檢查虛擬環境是否啟動
2. **Connection Refused**: 確認 Flask 服務正在運行
3. **Database Locked**: 檢查是否有其他進程使用數據庫
4. **Template Not Found**: 確認 templates 目錄結構

### 緊急重啟步驟
```bash
# 1. 關閉所有相關進程
pkill -f "python main_full.py"

# 2. 重新啟動
cd /home/weschen/HK_insurance/hk-ia-function
source venv/bin/activate
python main_full.py
```

## 📞 支援資源

### 相關文檔
- `README.md` - 基本說明
- `EMAIL_VERIFICATION.md` - 郵件驗證
- `ADMIN_SETUP_COMPLETE.md` - 管理員設置

### 備份位置
- **數據庫備份**：`aml_profiles_old.db`
- **代碼備份**：各種 `main_*.py` 版本

---

## 🎯 下一步工作

1. **Chrome 瀏覽器測試**：確認 http://127.0.0.1:5000 正常訪問
2. **功能驗證**：測試會員註冊、登入、查詢流程
3. **代碼標注**：在瀏覽器中查看系統並進行代碼註解

**最後更新**：2025年9月5日
**負責人**：GitHub Copilot Team
**狀態**：Ready for handover ✅
